from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("paid", "Pagada"),
        ("canceled", "Cancelada"),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    email = models.EmailField()
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)

    # Envío / dirección
    address_line1 = models.CharField("Dirección", max_length=200)
    address_line2 = models.CharField("Complemento", max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField("Departamento/Estado", max_length=100, blank=True)
    postal_code = models.CharField("Código Postal", max_length=20, blank=True)
    country = models.CharField(max_length=60, default="Colombia")

    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} – {self.user} – {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product} x{self.quantity}"
