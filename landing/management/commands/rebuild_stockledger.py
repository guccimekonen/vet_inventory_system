from django.core.management.base import BaseCommand
from landing.models import ShipmentItem
from sales.models import Sale
from inventory.models import StockLedger

class Command(BaseCommand):
    help = 'Rebuild StockLedger from existing Shipments and Sales'

    def handle(self, *args, **kwargs):
        # Clear existing ledger
        StockLedger.objects.all().delete()
        self.stdout.write("Cleared StockLedger...")

        # Add all shipment items
        for item in ShipmentItem.objects.all():
            StockLedger.objects.create(
                product=item.product,
                batch_number=item.batch_number,
                expiry_date=item.expiry_date,
                movement_type='IN',
                quantity=item.quantity,
                unit_cost=item.unit_landed_cost,
                total_cost=(item.unit_landed_cost or 0) * (item.quantity or 0),
                reference=f"Shipment {item.shipment.reference}"
            )
        self.stdout.write("Added all shipment items...")

        # Add all sales
        for sale in Sale.objects.all():
            StockLedger.objects.create(
                product=sale.product,
                batch_number=sale.get_batch_number(),
                expiry_date=None,
                movement_type='OUT',
                quantity=sale.quantity,
                unit_cost=sale._unit_cost or 0,
                total_cost=(sale._unit_cost or 0) * (sale.quantity or 0),
                reference=f"Sale ID {sale.id}"
            )
        self.stdout.write("Added all sales...")
        self.stdout.write(self.style.SUCCESS("StockLedger rebuilt successfully!"))
