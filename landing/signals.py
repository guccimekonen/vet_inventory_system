from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ShipmentItem
from inventory.models import StockLedger
from sales.models import Sale


@receiver(post_save, sender=ShipmentItem)
def create_or_update_stockledger_from_shipment(sender, instance, created, **kwargs):
    """
    Keep StockLedger IN rows synced with ShipmentItem landed cost in ETB.
    """
    instance.refresh_from_db()

    unit_cost = Decimal(instance.unit_landed_cost or 0)
    quantity = Decimal(instance.quantity or 0)

    StockLedger.objects.update_or_create(
        product=instance.product,
        batch_number=instance.batch_number,
        movement_type="IN",
        reference=f"Shipment {instance.shipment.reference}",
        defaults={
            "expiry_date": instance.expiry_date,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": unit_cost * quantity,
        },
    )


@receiver(post_save, sender=Sale)
def create_or_update_stockledger_from_sale(sender, instance, created, **kwargs):
    """
    Only APPROVED sales create stock-out ledger entries.
    Pending/rejected sales do not affect stock ledger.
    Batch-level allocations create one OUT row per consumed batch.
    """
    sale_reference = f"Sale #{instance.id}"

    if instance.status != Sale.STATUS_APPROVED or not instance.stock_applied:
        StockLedger.objects.filter(
            movement_type="OUT",
            reference=sale_reference,
        ).delete()
        return

    StockLedger.objects.filter(
        movement_type="OUT",
        reference=sale_reference,
    ).delete()

    allocations = list(instance.allocations.all())

    if allocations:
        StockLedger.objects.bulk_create([
            StockLedger(
                product=instance.product,
                batch_number=allocation.batch_number,
                expiry_date=allocation.expiry_date,
                movement_type="OUT",
                quantity=Decimal(allocation.quantity or 0),
                unit_cost=Decimal(allocation.unit_cost or 0),
                total_cost=Decimal(allocation.total_cost or 0),
                reference=sale_reference,
            )
            for allocation in allocations
        ])
        return

    unit_cost = Decimal(instance._unit_cost or 0)
    quantity = Decimal(instance.quantity or 0)

    StockLedger.objects.create(
        product=instance.product,
        batch_number=instance.consumed_batch_number or "",
        expiry_date=instance.consumed_expiry_date,
        movement_type="OUT",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=unit_cost * quantity,
        reference=sale_reference,
    )
