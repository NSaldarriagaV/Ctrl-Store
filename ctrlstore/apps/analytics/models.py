from django.db import models
from django.utils import timezone

class ProductSalesAggregate(models.Model):
    """
    Acumulado total de ventas por producto (unidades y revenue).
    """
    #  USAR STRING LAZY EN VEZ DE apps.get_model
    product = models.OneToOneField(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="sales_agg",
    )
    units_sold = models.BigIntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["units_sold"]),
            models.Index(fields=["revenue"]),
        ]

    def __str__(self):
        return f"{self.product} – {self.units_sold} uds"


class ProcessedOrder(models.Model):
    """
    Marca que una Order (paid) ya fue contabilizada en analytics
    para asegurar idempotencia incluso si el signal corre varias veces.
    """
    # USAR STRING LAZY
    order = models.OneToOneField(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="analytics_processed",
    )
    processed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Processed order #{self.order_id}"
