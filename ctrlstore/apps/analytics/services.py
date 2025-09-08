from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.apps import apps

from .models import ProductSalesAggregate, ProcessedOrder

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
