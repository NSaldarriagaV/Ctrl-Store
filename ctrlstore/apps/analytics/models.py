from django.db import models
from django.utils import timezone

class ProductSalesAggregate(models.Model):
    """
    Acumulado total de ventas por producto (unidades y revenue).
    """
    # 🔁 USAR STRING LAZY EN VEZ DE apps.get_model
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
    # 🔁 USAR STRING LAZY
    order = models.OneToOneField(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="analytics_processed",
    )
    processed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Processed order #{self.order_id}"

class ProductView(models.Model):
    """
    Registro de vistas de producto (click o visita al detail).
    """
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey("authx.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="product_views")

    # Para deduplicación ligera
    session_key = models.CharField(max_length=40, db_index=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ua_hash = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["session_key", "product", "created_at"]),
        ]

    def __str__(self):
        who = self.user or self.session_key or self.ip_address or "anon"
        return f"View({self.product_id} by {who} at {self.created_at:%Y-%m-%d %H:%M})"


class ProductViewAggregate(models.Model):
    """
    Acumulado global de vistas por producto (para top rápido).
    """
    product = models.OneToOneField("catalog.Product", on_delete=models.CASCADE, related_name="views_agg")
    views_count = models.BigIntegerField(default=0)
    last_view_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["views_count"]),
        ]

    def __str__(self):
        return f"{self.product} – {self.views_count} vistas"