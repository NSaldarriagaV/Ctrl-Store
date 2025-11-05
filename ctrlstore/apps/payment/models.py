from __future__ import annotations
from django.db import models
from django.utils import timezone
from typing import Any
from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = [
        ("initiated", "Iniciado"),
        ("captured", "Capturado"),
        ("failed", "Fallido"),
        ("refunded", "Reembolsado"),
    ]
    METHOD_CHOICES = [("card", "Tarjeta")]

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=6, default="COP")
    method = models.CharField(max_length=12, choices=METHOD_CHOICES, default="card")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="initiated")

    # Nunca guardes PAN/CVV. Solo derivados seguros:
    brand = models.CharField(max_length=12, blank=True)
    last4 = models.CharField(max_length=4, blank=True)

    # Autorización simulada
    auth_code = models.CharField(max_length=16, blank=True)
    error_code = models.CharField(max_length=32, blank=True)
    error_message = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Payment #{self.pk} - {self.status}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)