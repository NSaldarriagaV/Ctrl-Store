from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("ctrlstore.apps.catalog.urls", "catalog"), namespace="catalog")),
    path("auth/", include(("ctrlstore.apps.authx.urls", "authx"), namespace="authx")),
]
