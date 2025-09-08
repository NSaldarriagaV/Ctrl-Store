# ctrlstore/apps/cart/utils.py
from django.apps import apps
from .models import Cart

Product = apps.get_model("catalog", "Product")

def _ensure_session(request):
    if not request.session.session_key:
        request.session.save()

def get_or_create_cart(request):
    """
    - Invitado: guarda/ubica por session_key y memoriza anon_cart_id en la sesión.
    - Usuario logueado: prioriza user; mergea con carrito anónimo si existe (por session_key y/o anon_cart_id).
    """
    _ensure_session(request)
    session_key = request.session.session_key

    if request.user.is_authenticated:
        # Carrito del usuario
        cart_user, _ = Cart.objects.get_or_create(user=request.user)

        # 1) Merge por session_key antiguo (quizá no sirva tras login por rotación, pero lo intentamos)
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

        # 2) Merge por anon_cart_id guardado en sesión (robusto frente a rotación de sesión)
        anon_cart_id = request.session.get("anon_cart_id")
        if anon_cart_id:
            try:
                cart_session2 = Cart.objects.get(id=anon_cart_id, user__isnull=True)
                if cart_session2.id != cart_user.id:
                    for item in cart_session2.items.all():
                        tgt, created = cart_user.items.get_or_create(
                            product=item.product,
                            defaults={"quantity": item.quantity, "unit_price": item.unit_price},
                        )
                        if not created:
                            tgt.quantity += item.quantity
                            tgt.save()
                    cart_session2.delete()
            except Cart.DoesNotExist:
                pass
            finally:
                # Limpia el marcador
                request.session.pop("anon_cart_id", None)

        return cart_user

    # Invitado: crea/recupera por session_key y guarda anon_cart_id en la sesión
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
    # marca el carrito anónimo activamente en la sesión para supervivencia post-login
    request.session["anon_cart_id"] = cart.id
    return cart
