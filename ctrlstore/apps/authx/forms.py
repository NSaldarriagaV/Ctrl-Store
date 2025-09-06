from __future__ import annotations

from typing import Optional

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. Ingresa una dirección de email válida.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self) -> str:
        email: str = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("El email es obligatorio.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        
        # Asignar rol de Cliente por defecto
        try:
            from .models import Role
            cliente_role = Role.objects.get(name="Cliente")
            user.role = cliente_role
        except Role.DoesNotExist:
            # Si no existe el rol Cliente, crear uno por defecto
            cliente_role = Role.objects.create(
                name="Cliente",
                description="Acceso básico de compras",
                is_active=True
            )
            user.role = cliente_role
        
        if commit:
            user.save()
        
        return user


class UserEditForm(forms.ModelForm):
    """Formulario para editar usuarios desde el panel de administración."""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
