from __future__ import annotations

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import SignupView

app_name = "authx"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="authx/login.html"), name="login"),
    path("logout/", LogoutView.as_view(template_name="authx/logged_out.html"), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
]
