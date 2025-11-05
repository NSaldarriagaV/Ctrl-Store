from __future__ import annotations

from typing import Any

import io

from django.apps import apps
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.db import transaction
from django.db.models import F
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone
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
def pay(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Limpia mensajes antiguos (del carrito/checkout) para esta vista
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
def process(request: HttpRequest, order_id: int) -> HttpResponse | HttpResponseRedirect:
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Idempotencia: si ya está paga, no reprocesar
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
    number: str = cd["card_number"]
    brand: str = cd.get("brand", "card")

    # Crear Payment en estado initiated (sin almacenar PAN/CVV)
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
                faltantes: list[str] = []
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
                    update_fields=[
                        "status",
                        "auth_code",
                        "error_code",
                        "error_message",
                        "updated_at",
                    ]
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

    # Fallo en la autorización
    payment.status = "failed"
    payment.error_code = getattr(result, "error_code", None) or "error"
    payment.error_message = getattr(result, "msg", None) or "No fue posible procesar el pago."
    payment.save(update_fields=["status", "error_code", "error_message", "updated_at"])

    messages.error(request, payment.error_message)
    return render(request, "payment/pay.html", {"order": order, "form": form})


@login_required
@require_GET
def confirm(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = get_object_or_404(Payment, pk=payment_id, order__user=request.user)
    order = payment.order
    items = order.items.select_related("product")
    return render(request, "payment/confirm.html", {"payment": payment, "order": order, "items": items})


def render_to_pdf(template_src: str, context: dict[str, Any]) -> HttpResponse | None:
    """Helper: render un template HTML a PDF (None si no hay dependencia disponible)."""
    try:
        from xhtml2pdf import pisa  # type: ignore
    except Exception:
        return None
    template = get_template(template_src)
    html = template.render(context)
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=result, encoding="utf-8")
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")
    return None


@login_required
@require_GET
def invoice_pdf(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = get_object_or_404(Payment, pk=payment_id, order__user=request.user)
    if payment.status != "captured":
        return HttpResponseBadRequest("La factura solo está disponible para pagos aprobados.")
    order = payment.order
    items = order.items.select_related("product")

    created_local = timezone.localtime(payment.created_at)
    invoice_number = f"INV-{payment.id}-{created_local.strftime('%Y%m%d')}"
    context: dict[str, Any] = {
        "invoice_number": invoice_number,
        "created_at": created_local,
        "payment": payment,
        "order": order,
        "items": items,
        # Datos del emisor (ajusta a tu negocio)
        "company": {
            "name": "Ctrl+Store S.A.S.",
            "tax_id": "NIT 900.000.000-1",
            "address": "Calle 123 #45-67, Medellín, Colombia",
            "email": "facturacion@ctrlstore.com",
            "phone": "+57 300 000 0000",
        },
    }

    pdf_resp = render_to_pdf("payment/invoice.html", context)
    if pdf_resp is None:
        raise Http404("No se pudo generar el PDF.")

    filename = f"Factura-{invoice_number}.pdf"
    pdf_resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return pdf_resp
