from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from ctrlstore.apps.order.models import Order
from .forms import CardPaymentForm
from .models import Payment
from .services import simulate_authorize

from django.db import transaction
from django.db.models import F
from django.apps import apps


@login_required
@require_GET
def pay(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # 🔹 Limpia mensajes antiguos (del carrito/checkout) para esta vista
    storage = get_messages(request)
    for _ in storage:
        pass  # consumirlos para que no se muestren aquí

    if order.status == "paid":
        last_payment = order.payments.first()
        if last_payment:
            return redirect("payment:confirm", payment_id=last_payment.id)
        return redirect("order:checkout")

    form = CardPaymentForm()
    return render(request, "payment/pay.html", {"order": order, "form": form})


@login_required
@require_POST
def process(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Idempotencia básica: si ya está paga, no reprocesar
    if order.status == "paid":
        last_payment = order.payments.first()
        if last_payment:
            return redirect("payment:confirm", payment_id=last_payment.id)
        messages.info(request, "La orden ya estaba pagada.")
        return redirect("order:checkout")

    form = CardPaymentForm(request.POST)
    if not form.is_valid():
        return render(request, "payment/pay.html", {"order": order, "form": form})

    cd = form.cleaned_data
    number = cd["card_number"]
    brand = cd.get("brand", "card")

    # Crear Payment en estado initiated (no guardar PAN/CVV)
    payment = Payment.objects.create(
        order=order,
        amount=order.total_amount,
        currency="COP",
        method="card",
        status="initiated",
        brand=brand,
        last4=number[-4:],
    )

    # Autorizar (simulado)
    result = simulate_authorize(number, float(order.total_amount), currency="COP")

    if result.ok:
        # Captura + actualización de inventario (transacción segura)
        try:
            with transaction.atomic():
                Product = apps.get_model("catalog", "Product")

                item_qs = order.items.select_related("product")
                product_ids = list(item_qs.values_list("product_id", flat=True))

                # Bloquea filas de producto para evitar carreras
                products = {
                    p.id: p
                    for p in Product.objects.select_for_update().filter(id__in=product_ids)
                }

                # 1) Validar stock suficiente
                faltantes = []
                for it in item_qs:
                    p = products.get(it.product_id)
                    if p is None:
                        faltantes.append(f"Producto {it.product_id} no existe")
                        continue
                    if getattr(p, "stock_quantity") < it.quantity:
                        faltantes.append(
                            f"{p} (stock: {getattr(p,'stock_quantity')}, requerido: {it.quantity})"
                        )

                if faltantes:
                    raise ValueError("Stock insuficiente para: " + ", ".join(faltantes))

                # 2) Descontar stock (operación atómica)
                for it in item_qs:
                    Product.objects.filter(pk=it.product_id).update(
                        stock_quantity=F("stock_quantity") - it.quantity
                    )

                # 3) Marcar pago/orden como exitosos
                payment.status = "captured"
                payment.auth_code = result.auth_code or "OK"
                payment.error_code = ""
                payment.error_message = ""
                payment.save(
                    update_fields=["status", "auth_code", "error_code", "error_message", "updated_at"]
                )

                order.status = "paid"
                order.save(update_fields=["status", "updated_at"])

        except Exception as e:
            # Revertir y mostrar error
            payment.status = "failed"
            payment.error_code = "out_of_stock"
            payment.error_message = str(e) or "No hay stock suficiente."
            payment.save(
                update_fields=["status", "error_code", "error_message", "updated_at"]
            )

            messages.error(request, payment.error_message)
            return render(request, "payment/pay.html", {"order": order, "form": form})

        messages.success(request, "Pago realizado con éxito.")
        return redirect("payment:confirm", payment_id=payment.id)

    # Fallo
    payment.status = "failed"
    payment.error_code = result.error_code or "error"
    payment.error_message = result.msg or "No fue posible procesar el pago."
    payment.save(update_fields=["status", "error_code", "error_message", "updated_at"])

    messages.error(request, payment.error_message)
    return render(request, "payment/pay.html", {"order": order, "form": form})


@login_required
@require_GET
def confirm(request, payment_id: int):
    payment = get_object_or_404(Payment, pk=payment_id, order__user=request.user)
    order = payment.order
    # Mostramos resumen del pedido, costo, datos de checkout y método de pago (enmascarado)
    items = order.items.select_related("product")
    return render(request, "payment/confirm.html", {"payment": payment, "order": order, "items": items})
