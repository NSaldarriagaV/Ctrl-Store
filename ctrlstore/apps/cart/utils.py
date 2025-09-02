from django.apps import apps
from .models import Cart

# 👇 obtenemos el modelo de catalog dinámicamente
Product = apps.get_model("catalog", "Product")


def _ensure_session(request):
    if not request.session.session_key:
        request.session.save()


def get_or_create_cart(request):
    """
    - Invitado: guarda/ubica por session_key
    - Usuario logueado: prioriza user; mergea con session si existe
    """
    _ensure_session(request)
    session_key = request.session.session_key

    if request.user.is_authenticated:
        # Carrito asociado al usuario
        cart_user, _ = Cart.objects.get_or_create(user=request.user)

        # Merge si había carrito de sesión anónimo
        try:
            cart_session = Cart.objects.get(session_key=session_key, user__isnull=True)
            if cart_session.id != cart_user.id:
                for item in cart_session.items.all():
                    tgt, created = cart_user.items.get_or_create(
                        product=item.product,
                        defaults={"quantity": item.quantity, "unit_price": item.unit_price},
                    )
                    if not created:
                        tgt.quantity += item.quantity
                        tgt.save()
                cart_session.delete()
        except Cart.DoesNotExist:
            pass

        return cart_user

    # Invitado
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
    return cart
