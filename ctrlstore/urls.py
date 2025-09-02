from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("ctrlstore.apps.catalog.urls", "catalog"), namespace="catalog")),
    path("auth/", include(("ctrlstore.apps.authx.urls", "authx"), namespace="authx")),
    path("cart/", include("ctrlstore.apps.cart.urls", namespace="cart")),
    path("order/", include("ctrlstore.apps.order.urls", namespace="order")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)