from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path("pay/<int:order_id>/", views.pay, name="pay"),
    path("pay/<int:order_id>/process/", views.process, name="process"),
    path("confirm/<int:payment_id>/", views.confirm, name="confirm"),
    path("invoice/<int:payment_id>/", views.invoice_pdf, name="invoice_pdf"),
]
