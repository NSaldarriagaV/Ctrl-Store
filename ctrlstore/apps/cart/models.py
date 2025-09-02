from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Cart(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["session_key"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        who = self.user or self.session_key or "anon"
        return f"Cart({who})"

    @property
    def items_count(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def total(self):
        return sum(i.subtotal for i in self.items.select_related("product"))


class CartItem(models.Model):
    cart = models.ForeignKey("cart.Cart", related_name="items", on_delete=models.CASCADE)
    # 👇 referencia limpia al modelo de otra app
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
