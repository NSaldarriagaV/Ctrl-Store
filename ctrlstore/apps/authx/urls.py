from __future__ import annotations

from django.urls import path

from .views import (
    AdminDashboardView,
    AdminRolesView,
    AdminUsersView,
    AdminProductsView,
    AdminProductCreateView,
    AdminProductEditView,
    AdminProductDeleteView,
    AdminCategoriesView,
    CustomLoginView,
    CustomLogoutView,
    SignupView,
    UserDetailView,
    UserEditView,
    UserToggleStatusView,
    AdminSalesHistoryView,
    AdminSalesReportView,
    AdminSalesExportCSVView
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
    
    # Gestión de productos
    path("admin/products/", AdminProductsView.as_view(), name="admin_products"),
    path("admin/products/create/", AdminProductCreateView.as_view(), name="admin_product_create"),
    path("admin/products/<int:product_id>/edit/", AdminProductEditView.as_view(), name="admin_product_edit"),
    path("admin/products/<int:product_id>/delete/", AdminProductDeleteView.as_view(), name="admin_product_delete"),
    path("admin/categories/", AdminCategoriesView.as_view(), name="admin_categories"),
    
    # Acciones de usuarios
    path("admin/users/<int:user_id>/detail/", UserDetailView.as_view(), name="user_detail"),
    path("admin/users/<int:user_id>/edit/", UserEditView.as_view(), name="user_edit"),
    path("admin/users/<int:user_id>/toggle-status/", UserToggleStatusView.as_view(), name="user_toggle_status"),

    # Reportes de ventas
    path("admin/sales/", AdminSalesHistoryView.as_view(), name="admin_sales"),
    path("admin/sales/report/", AdminSalesReportView.as_view(), name="admin_sales_report"),
    path("admin/sales/export.csv", AdminSalesExportCSVView.as_view(), name="admin_sales_export"),
]
