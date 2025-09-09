from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.apps import apps

from .services import record_order_paid

Order = apps.get_model("order", "Order")


@receiver(post_save, sender=Order)
def handle_order_paid(sender, instance: Order, created: bool, **kwargs):
    """
    Cuando una orden cambia a 'paid', registramos ventas al commit de la transacción.
    """
    if instance.status == "paid":
        transaction.on_commit(lambda: record_order_paid(instance.id))
