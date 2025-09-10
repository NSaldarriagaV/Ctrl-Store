from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ctrlstore.apps.common.exceptions import CartError, StockError
from ctrlstore.apps.common.logging_config import cart_logger

from .models import CartItem
from .services import CartService, CartValidationService
from .utils import get_or_create_cart

# 👇 obtenemos el modelo dinámicamente
Product = apps.get_model("catalog", "Product")


def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")
    return render(request, "cart/cart-detail.html", {"cart": cart, "items": items})


@require_POST
def add_to_cart(request, product_id):
    """Agrega un producto al carrito usando el servicio."""
    product = get_object_or_404(Product, pk=product_id)

    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Cantidad inválida")

    qty = max(1, qty)

    try:
        item = CartService.add_to_cart(request, product, qty)
        messages.success(request, f"{product.name} agregado al carrito.")

        cart_logger.log_cart_operation(
            "add_product",
            cart_id=item.cart.id,
            user_id=request.user.id if request.user.is_authenticated else None,
            product_id=product.id,
            product_name=product.name,
            quantity=qty,
        )

    except (StockError, CartError) as e:
        messages.error(request, str(e))
        cart_logger.log_error(
            e,
            {
                "action": "add_to_cart",
                "product_id": product.id,
                "quantity": qty,
                "user_id": request.user.id if request.user.is_authenticated else None,
            },
        )
    except Exception as e:
        messages.error(request, "Error al agregar producto al carrito.")
        cart_logger.log_error(
            e, {"action": "add_to_cart", "product_id": product.id, "quantity": qty}
        )

    return redirect(request.POST.get("next") or "cart:detail")


@require_POST
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Cantidad inválida")

    if qty <= 0:
        item.delete()
        messages.info(request, f"{item.product.name} eliminado del carrito.")
    else:
        if (
            hasattr(item.product, "stock")
            and item.product.stock is not None
            and qty > item.product.stock
        ):
            messages.error(request, "No hay stock suficiente.")
        else:
            item.quantity = qty
            item.save()
            messages.success(request, f"Cantidad actualizada: {item.product.name} x{qty}")
    return redirect("cart:detail")


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, "Producto eliminado del carrito.")
    return redirect("cart:detail")
