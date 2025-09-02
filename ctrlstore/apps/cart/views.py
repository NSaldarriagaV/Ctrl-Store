from decimal import Decimal

from django.apps import apps
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import CartItem
from .utils import get_or_create_cart

# 👇 obtenemos el modelo dinámicamente
Product = apps.get_model("catalog", "Product")


def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")
    return render(request, "cart/cart_detail.html", {"cart": cart, "items": items})


@require_POST
def add_to_cart(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, pk=product_id)

    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Cantidad inválida")

    qty = max(1, qty)

    # Validar stock opcional
    if hasattr(product, "stock") and product.stock is not None:
        if qty > product.stock:
            messages.error(request, "No hay stock suficiente.")
            return redirect(request.POST.get("next") or "cart:detail")

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": qty, "unit_price": Decimal(product.price)},
    )
    if not created:
        item.quantity += qty
        item.save()

    messages.success(request, f"{product.name} agregado al carrito.")
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
        if hasattr(item.product, "stock") and item.product.stock is not None and qty > item.product.stock:
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
