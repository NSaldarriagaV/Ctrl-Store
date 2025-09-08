from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(label="Nombre completo", max_length=120)
    email = forms.EmailField(label="Correo")
    phone = forms.CharField(label="Teléfono", max_length=30, required=False)

    address_line1 = forms.CharField(label="Dirección", max_length=200)
    address_line2 = forms.CharField(label="Complemento", max_length=200, required=False)
    city = forms.CharField(label="Ciudad", max_length=100)
    state = forms.CharField(label="Departamento/Estado", max_length=100, required=False)
    postal_code = forms.CharField(label="Código Postal", max_length=20, required=False)
    country = forms.CharField(label="País", max_length=60, initial="Colombia")
