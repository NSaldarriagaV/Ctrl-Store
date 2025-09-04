from django import forms
import re
from .services import validate_card_number, detect_brand, validate_expiry, validate_cvv

DARK_INPUT = {"class": "form-control bg-dark text-light border-secondary", "style": "width:100%;"}

class CardPaymentForm(forms.Form):
    cardholder_name = forms.CharField(
        label="Titular", max_length=120,
        widget=forms.TextInput(attrs={**DARK_INPUT, "id":"id_cardholder_name", "placeholder":"Nombre como en la tarjeta", "autocomplete":"off"}),
    )
    card_number = forms.CharField(
        label="Número de tarjeta", max_length=19,
        widget=forms.TextInput(attrs={**DARK_INPUT, "id":"id_card_number", "inputmode":"numeric", "placeholder":"•••• •••• •••• ••••", "autocomplete":"off"}),
    )
    expiry = forms.CharField(
        label="Vencimiento (MM/YY)", max_length=5,
        widget=forms.TextInput(attrs={**DARK_INPUT, "id":"id_expiry", "placeholder":"MM/YY", "inputmode":"numeric", "autocomplete":"off"}),
    )
    cvv = forms.CharField(
        label="CVV", max_length=4,
        widget=forms.TextInput(attrs={**DARK_INPUT, "id":"id_cvv", "inputmode":"numeric", "placeholder":"CVV", "autocomplete":"off"}),
    )
    zip_code = forms.CharField(
        label="Código Postal (opcional)", max_length=10, required=False,
        widget=forms.TextInput(attrs={**DARK_INPUT, "id":"id_zip", "placeholder":"Código Postal", "autocomplete":"off"}),
    )

    def clean_card_number(self):
        raw = self.cleaned_data["card_number"]
        number = re.sub(r"\D", "", raw)  # ← deja solo dígitos (acepta espacios)
        validate_card_number(number)
        return number

    def clean_expiry(self):
        raw = (self.cleaned_data.get("expiry") or "").strip().replace(" ", "")
        if len(raw) == 5 and "/" in raw:
            mm, yy = raw.split("/", 1)
        elif len(raw) == 4 and "/" not in raw:
            mm, yy = raw[:2], raw[2:]
        else:
            raise forms.ValidationError("Usa el formato MM/YY.")
        if not (mm.isdigit() and yy.isdigit()):
            raise forms.ValidationError("Usa dígitos en MM/YY.")
        month = int(mm)
        year2 = int(yy)
        year = year2 + (2000 if year2 < 100 else 0)
        validate_expiry(month, year)
        self.cleaned_data["expiry_month"] = month
        self.cleaned_data["expiry_year"] = year
        return raw

    def clean(self):
        cleaned = super().clean()
        number = cleaned.get("card_number")
        cvv = cleaned.get("cvv", "")
        if number and "expiry_month" in cleaned and "expiry_year" in cleaned:
            brand = detect_brand(number)
            validate_cvv(cvv, brand)
            cleaned["brand"] = brand
        return cleaned
