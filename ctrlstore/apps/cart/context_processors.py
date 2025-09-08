from .utils import get_or_create_cart

def cart_info(request):
    try:
        cart = get_or_create_cart(request)
        return {"cart_items_count": cart.items_count, "cart_total": cart.total}
    except Exception:
        return {"cart_items_count": 0, "cart_total": 0}
