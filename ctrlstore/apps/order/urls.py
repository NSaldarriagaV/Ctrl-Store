from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("pay/<int:order_id>/", views.pay, name="pay"),  # placeholder de pasarela
]
