from decimal import Decimal
from django.db import transaction
from django.db.models import F, Count
from django.apps import apps
import hashlib
from datetime import timedelta
from django.utils import timezone

from .models import ProductSalesAggregate, ProcessedOrder, ProductView, ProductViewAggregate

Product = apps.get_model("catalog", "Product")
Order = apps.get_model("order", "Order")
OrderItem = apps.get_model("order", "OrderItem")


def record_order_paid(order_id: int) -> None:
    """
    Incrementa los contadores de ventas por producto para la order pagada.
    Idempotente: usa ProcessedOrder para no contar dos veces.
    """
    with transaction.atomic():
        order = (
            Order.objects
            .select_for_update()
            .select_related("user")
            .get(pk=order_id)
        )

        # Si ya se procesó, salimos
        if ProcessedOrder.objects.filter(order=order).exists():
            return

        # Solo contabilizamos ordenes pagadas
        if order.status != "paid":
            return

        items = (
            OrderItem.objects
            .select_related("product")
            .filter(order=order)
        )

        for it in items:
            # Crea el acumulado si no existe
            agg, _ = ProductSalesAggregate.objects.get_or_create(
                product=it.product,
                defaults={
                    "units_sold": 0,
                    "revenue": Decimal("0.00"),
                },
            )
            # Actualiza en la BD (evita condiciones de carrera)
            ProductSalesAggregate.objects.filter(pk=agg.pk).update(
                units_sold=F("units_sold") + it.quantity,
                revenue=F("revenue") + (it.unit_price * it.quantity),
                last_paid_at=order.updated_at or order.created_at,
            )

        # Marca la orden como contabilizada
        ProcessedOrder.objects.create(order=order)

        Product = apps.get_model("catalog", "Product")


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _ua_hash(request):
    ua = (request.META.get("HTTP_USER_AGENT") or "").strip()
    return hashlib.sha256(ua.encode("utf-8")).hexdigest()[:40]


def record_product_view(request, product):
    """
    Registra una vista de producto con deduplicación por ventana (1 hora) por sesión/producto.
    """
    session_key = _ensure_session_key(request)
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    ip = _get_client_ip(request)
    uah = _ua_hash(request)

    now = timezone.now()
    window_start = now - timedelta(hours=1)

    # dedupe: ya registramos esta combinación (session, product) en la última hora?
    exists = ProductView.objects.filter(
        product=product,
        session_key=session_key,
        created_at__gte=window_start,
    ).exists()
    if exists:
        # Aunque no creemos un nuevo row, sí actualizamos last_view_at para el agregado.
        ProductViewAggregate.objects.filter(product=product).update(last_view_at=now)
        return False  # no creó nuevo evento

    with transaction.atomic():
        ProductView.objects.create(
            product=product,
            user=user,
            session_key=session_key,
            ip_address=ip,
            ua_hash=uah,
        )
        agg, _ = ProductViewAggregate.objects.get_or_create(product=product, defaults={"views_count": 0})
        ProductViewAggregate.objects.filter(pk=agg.pk).update(
            views_count=F("views_count") + 1,
            last_view_at=now,
        )
    return True


def top_viewed(limit=3, days=None):
    """
    Retorna los productos más vistos (global) con option de ventana temporal.
    - Si 'days' se especifica, calcula sobre ProductView (Count) en esa ventana.
    - Si no, usa el agregado global ProductViewAggregate.
    """
    Product = apps.get_model("catalog", "Product")  # evitar import circular

    if days:
        since = timezone.now() - timedelta(days=days)
        qs = (
            ProductView.objects.filter(created_at__gte=since)
            .values("product")
            .annotate(views=Count("id"))
            .order_by("-views")[:limit]
        )
        # Devuelve lista de (product, views)
        product_map = Product.objects.in_bulk([r["product"] for r in qs])
        return [(product_map[r["product"]], r["views"]) for r in qs]

    # Global (sin ventana): usa agregados
    aggs = (
        ProductViewAggregate.objects.select_related("product")
        .order_by("-views_count", "-last_view_at")[:limit]
    )
    return [(a.product, a.views_count) for a in aggs]
