from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("p/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    # API pública
    path("api/products/in-stock/", views.products_in_stock_api, name="api_products_in_stock"),
    
    # Productos aliados
    path("productos-aliados/", views.ProductosAliadosView.as_view(), name="productos_aliados"),
    
    # URLs del Comparador
    path("compare/", views.CompareCategorySelectView.as_view(), name="compare_category_select"),
    path("compare/category/<int:category_id>/", views.CompareProductSelectView.as_view(), name="compare_product_select"),
    path("compare/products/<int:product1_id>/vs/<int:product2_id>/", views.CompareProductsView.as_view(), name="compare_products"),
]
