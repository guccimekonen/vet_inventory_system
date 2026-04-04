from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ShipmentItem
from inventory.models import StockLedger  # corrected app
from sales.models import Sale

# -------------------------
# SHIPMENT → STOCKLEDGER (IN)
# -------------------------
@receiver(post_save, sender=ShipmentItem)
def create_stockledger_from_shipment(sender, instance, created, **kwargs):
    if created:
        StockLedger.objects.create(
            product=instance.product,
            batch_number=instance.batch_number,
            expiry_date=instance.expiry_date,
            movement_type='IN',
            quantity=instance.quantity,
            unit_cost=instance.unit_landed_cost,
            total_cost=(instance.unit_landed_cost or 0) * (instance.quantity or 0),
            reference=f"Shipment {instance.shipment.reference}"
        )

# -------------------------
# SALE → STOCKLEDGER (OUT)
# -------------------------
@receiver(post_save, sender=Sale)
def create_stockledger_from_sale(sender, instance, created, **kwargs):
    if created:
        StockLedger.objects.create(
            product=instance.product,
            batch_number=instance.get_batch_number(),
            expiry_date=None,  # optional
            movement_type='OUT',
            quantity=instance.quantity,
            unit_cost=instance._unit_cost or 0,
            total_cost=(instance._unit_cost or 0) * (instance.quantity or 0),
            reference=f"Sale ID {instance.id}"
        )
