from __future__ import annotations

from typing import Any, Dict
import re

from django import forms

from .services import (
    validate_card_number,
    detect_brand,
    validate_expiry,
    validate_cvv,
)

# i18n
from django.utils.translation import gettext_lazy as _

DARK_INPUT = {
    "class": "form-control bg-dark text-light border-secondary",
    "style": "width:100%;",
}


class CardPaymentForm(forms.Form):
    cardholder_name = forms.CharField(
        label="Titular",
        max_length=120,
        widget=forms.TextInput(
            attrs={
                **DARK_INPUT,
                "id": "id_cardholder_name",
                "placeholder": "Nombre como en la tarjeta",
                "autocomplete": "off",
            }
        ),
    )
    card_number = forms.CharField(
        label="Número de tarjeta",
        max_length=19,
        widget=forms.TextInput(
            attrs={
                **DARK_INPUT,
                "id": "id_card_number",
                "inputmode": "numeric",
                "placeholder": "•••• •••• •••• ••••",
                "autocomplete": "off",
            }
        ),
    )
    expiry = forms.CharField(
        label="Vencimiento (MM/YY)",
        max_length=5,
        widget=forms.TextInput(
            attrs={
                **DARK_INPUT,
                "id": "id_expiry",
                "placeholder": "MM/YY",
                "inputmode": "numeric",
                "autocomplete": "off",
            }
        ),
    )
    cvv = forms.CharField(
        label="CVV",
        max_length=4,
        widget=forms.TextInput(
            attrs={
                **DARK_INPUT,
                "id": "id_cvv",
                "inputmode": "numeric",
                "placeholder": "CVV",
                "autocomplete": "off",
            }
        ),
    )
    zip_code = forms.CharField(
        label=_("Código Postal (opcional)"),
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                **DARK_INPUT,
                "id": "id_zip",
                "placeholder": _("Código Postal"),
                "autocomplete": "off",
            }
        ),
    )

    cleaned_data: Dict[str, Any]

    # --- Validaciones de campo ---

    def clean_card_number(self) -> str:
        raw: str = (self.cleaned_data.get("card_number") or "")
        number = re.sub(r"\D", "", raw)  # normaliza: solo dígitos
        validate_card_number(number)
        return number

    def clean_expiry(self) -> str:
        raw: str = (self.cleaned_data.get("expiry") or "").strip().replace(" ", "")
        if len(raw) == 5 and "/" in raw:
            mm, yy = raw.split("/", 1)
        elif len(raw) == 4 and "/" not in raw:
            mm, yy = raw[:2], raw[2:]
        else:
            raise forms.ValidationError(_("Usa el formato MM/YY."))
        if not (mm.isdigit() and yy.isdigit()):
            raise forms.ValidationError(_("Usa dígitos en MM/YY."))
        month = int(mm)
        year2 = int(yy)
        year = year2 + (2000 if year2 < 100 else 0)
        validate_expiry(month, year)
        # Guarda parseo para validaciones cruzadas
        self.cleaned_data["expiry_month"] = month
        self.cleaned_data["expiry_year"] = year
        return raw

    def clean_cvv(self) -> str:
        value: str = (self.cleaned_data.get("cvv") or "").strip()
        # La validación final de CVV depende de la marca; la hacemos en clean()
        if not value:
            raise forms.ValidationError("CVV requerido.")
        if not value.isdigit():
            raise forms.ValidationError("CVV inválido.")
        return value

    # --- Validación cruzada del formulario ---

    def clean(self) -> Dict[str, Any]:
        data: Dict[str, Any] = dict(super().clean() or {})

        number: str = data.get("card_number", "") or ""
        cvv: str = data.get("cvv", "") or ""

        # Si ya parseamos MM/YY arriba, tendremos estas llaves
        month = data.get("expiry_month")
        year = data.get("expiry_year")

        # Validación cruzada de marca + CVV
        if number and isinstance(month, int) and isinstance(year, int):
            brand = detect_brand(number)
            validate_cvv(cvv, brand)
            data["brand"] = brand

        return data
