from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from landing.models import ShipmentItem
from sales.models import Sale
from .models import StockLedger

# =========================
# STOCK IN SIGNAL
# =========================
@receiver(post_save, sender=ShipmentItem)
def create_stock_in(sender, instance, created, **kwargs):
    """
    Automatically create a StockLedger IN entry whenever a new ShipmentItem is added.
    """
    if created:
        StockLedger.objects.create(
            product=instance.product,
            batch_number=instance.batch_number or "",
            expiry_date=instance.expiry_date,
            movement_type='IN',
            quantity=Decimal(instance.quantity or 0),
            unit_cost=Decimal(instance.unit_landed_cost or 0),
            reference=f"Shipment {instance.shipment.reference}"
        )

# =========================
# STOCK OUT SIGNAL
# =========================
@receiver(post_save, sender=Sale)
def create_stock_out(sender, instance, created, **kwargs):
    """
    Automatically create a StockLedger OUT entry whenever a new Sale is recorded.
    Uses FIFO-consumed unit cost (_unit_cost) stored in Sale.
    """
    if created:
        StockLedger.objects.create(
            product=instance.product,
            movement_type='OUT',
            quantity=Decimal(instance.quantity or 0),
            unit_cost=Decimal(instance._unit_cost or 0),
            reference=f"Sale {instance.id}"
        )
