from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, render, resolve_url, get_object_or_404
from django.urls import reverse, NoReverseMatch

from ctrlstore.apps.cart.utils import get_or_create_cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def _login_with_next_url() -> str:
    """
    Construye la URL de login existente en authx con ?next=/order/checkout/.
    No modifica authx ni depende de settings; usa el name namespaced 'authx:login'.
    """
    try:
        login_url = reverse("authx:login")
    except NoReverseMatch:
        login_url = "/auth/login/"
    next_url = reverse("order:checkout")
    return f"{login_url}?next={next_url}"


def _require_logged_in(request):
    if not request.user.is_authenticated:
        return redirect(_login_with_next_url())
    return None


def _cart_must_have_items(cart, request):
    if cart.items.count() == 0:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("cart:detail")
    return None


def checkout(request):
    # 1) Requiere login (redirige a authx:login con ?next=/order/checkout/)
    maybe_redirect = _require_logged_in(request)
    if maybe_redirect:
        return maybe_redirect

    # 2) Traer carrito y validar que tenga ítems
    cart = get_or_create_cart(request)
    maybe_redirect = _cart_must_have_items(cart, request)
    if maybe_redirect:
        return maybe_redirect

    # 3) Prefill con datos del usuario (correo visible y editable solo si tú quieres)
    initial = {
        "email": getattr(request.user, "email", "") or "",
        "full_name": getattr(request.user, "get_full_name", lambda: "")() or "",
        "country": "Colombia",
    }

    shipping = Decimal("15.00")  # ajusta tu lógica de envío si aplica
    
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # 4) Calcular totales
            subtotal = sum(i.subtotal for i in cart.items.select_related("product"))
            total = subtotal + shipping

            # 5) Crear Order + OrderItems
            order = Order.objects.create(
                user=request.user,
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data.get("phone", ""),
                address_line1=form.cleaned_data["address_line1"],
                address_line2=form.cleaned_data.get("address_line2", ""),
                city=form.cleaned_data["city"],
                state=form.cleaned_data.get("state", ""),
                postal_code=form.cleaned_data.get("postal_code", ""),
                country=form.cleaned_data.get("country", "Colombia"),
                subtotal_amount=subtotal,
                shipping_amount=shipping,
                total_amount=total,
                status="pending",
            )

            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=ci.product,
                    quantity=ci.quantity,
                    unit_price=ci.unit_price,
                    line_total=ci.unit_price * ci.quantity,
                )
                for ci in cart.items.select_related("product")
            ])

            # (Opcional) Vaciar carrito
            cart.items.all().delete()

            messages.success(request, "Orden creada correctamente. Continúa con el pago.")
            return redirect("order:pay", order_id=order.id)
    else:
        form = CheckoutForm(initial=initial)

    items = cart.items.select_related("product")
    context = {
        "form": form,
        "cart": cart,
        "items": items,
        "subtotal": cart.total,
        "shipping": Decimal("15.00"),
        "grand_total": cart.total + shipping,  # suma shipping si lo aplicas
    }
    return render(request, "order/checkout.html", context)


def pay(request, order_id):
    # Placeholder para integrar tu pasarela (Wompi/PayU/Stripe)
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return redirect("payment:pay", order_id=order.id)

