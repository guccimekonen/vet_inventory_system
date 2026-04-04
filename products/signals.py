from django.db.models.signals import post_save
from django.dispatch import receiver
from landing.models import ShipmentItem
from .models import Product

@receiver(post_save, sender=ShipmentItem)
def update_product_unit_cost(sender, instance, **kwargs):
    """
    Every time a ShipmentItem is saved, update the Product's unit_cost
    based on all ShipmentItems for that product (weighted average).
    """
    if instance.product:
        instance.product.update_cost_from_shipments()
