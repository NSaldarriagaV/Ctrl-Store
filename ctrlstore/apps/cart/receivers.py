# ctrlstore/apps/cart/receivers.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart

@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    Combina el carrito anónimo (guardado en session['anon_cart_id'])
    con el carrito del usuario al iniciar sesión.
    """
    anon_cart_id = request.session.get("anon_cart_id")
    if not anon_cart_id:
        return

    try:
        cart_session = Cart.objects.get(id=anon_cart_id, user__isnull=True)
    except Cart.DoesNotExist:
        # Limpia el flag si ya no existe
        request.session.pop("anon_cart_id", None)
        return

    # Carrito del usuario
    cart_user, _ = Cart.objects.get_or_create(user=user)

    # Fusiona items (suma cantidades si el producto ya estaba)
    for item in cart_session.items.select_related("product"):
        tgt, created = cart_user.items.get_or_create(
            product=item.product,
            defaults={"quantity": item.quantity, "unit_price": item.unit_price},
        )
        if not created:
            tgt.quantity += item.quantity
            tgt.save()

    # Elimina el carrito anónimo y limpia la sesión
    cart_session.delete()
    request.session.pop("anon_cart_id", None)
