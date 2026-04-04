from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Sale
from inventory.models import StockLedger

@receiver(post_save, sender=Sale)
def create_stock_ledger_on_sale(sender, instance, created, **kwargs):
    """
    Automatically create StockLedger entry when a Sale is made.
    """
    if created:
        StockLedger.objects.create(
            product=instance.product,
            batch_number=instance.get_batch_number(),
            expiry_date=getattr(instance.product, 'expiry_date', None),
            movement_type='OUT',
            quantity=instance.quantity,
            unit_cost=instance.get_cost_price(),
            reference=f"Sale #{instance.id}",
        )
