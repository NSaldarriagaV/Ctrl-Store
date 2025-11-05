from django import forms
from django.utils.translation import gettext_lazy as _

class CheckoutForm(forms.Form):
    full_name = forms.CharField(label=_("Nombre completo"), max_length=120)
    email = forms.EmailField(label=_("Correo"))
    phone = forms.CharField(label=_("Teléfono"), max_length=30, required=False)

    address_line1 = forms.CharField(label=_("Dirección"), max_length=200)
    address_line2 = forms.CharField(label=_("Complemento"), max_length=200, required=False)
    city = forms.CharField(label=_("Ciudad"), max_length=100)
    state = forms.CharField(label=_("Departamento/Estado"), max_length=100, required=False)
    postal_code = forms.CharField(label=_("Código Postal"), max_length=20, required=False)
    country = forms.CharField(label=_("País"), max_length=60, initial=_("Colombia"))
