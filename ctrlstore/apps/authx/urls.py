from __future__ import annotations

from django.urls import path

from .views import (
    AdminDashboardView,
    AdminRolesView,
    AdminUsersView,
    CustomLoginView,
    CustomLogoutView,
    SignupView,
    UserDetailView,
    UserEditView,
    UserToggleStatusView,
)

app_name = "authx"

urlpatterns = [
    # Autenticación básica
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
    
    # Panel de administración
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin/users/", AdminUsersView.as_view(), name="admin_users"),
    path("admin/roles/", AdminRolesView.as_view(), name="admin_roles"),
    
    # Acciones de usuarios
    path("admin/users/<int:user_id>/detail/", UserDetailView.as_view(), name="user_detail"),
    path("admin/users/<int:user_id>/edit/", UserEditView.as_view(), name="user_edit"),
    path("admin/users/<int:user_id>/toggle-status/", UserToggleStatusView.as_view(), name="user_toggle_status"),
]
