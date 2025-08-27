from __future__ import annotations

from typing import Any

from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import SignupForm


class SignupView(FormView):
    template_name = "authx/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form: SignupForm) -> HttpResponse:
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

    # Opcional: hints explícitos para mypy/ruff (no requerido)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: D401
        """Renderiza el formulario de registro."""
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: D401
        """Procesa el envío del formulario de registro."""
        return super().post(request, *args, **kwargs)
