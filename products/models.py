from decimal import Decimal

from django.db import models


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50)
    batch_number = models.CharField(max_length=100, blank=True, null=True)

    # Supplier unit cost in USD
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    # Manual final selling price in ETB
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    profit_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    reorder_level = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    hs_code = models.CharField(max_length=50, blank=True, null=True)
    controlled = models.BooleanField(default=False)
    opening_quantity = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    def get_current_stock(self) -> int:
        from landing.models import ShipmentItem
        return sum(item.quantity_remaining or 0 for item in ShipmentItem.objects.filter(product=self))

    def get_total_purchased(self) -> int:
        return sum(p.quantity or 0 for p in self.purchase_set.all())

    
    def get_total_sold(self) -> int:
        from sales.models import Sale
        return sum(
            s.quantity or 0
            for s in Sale.objects.filter(product=self, status=Sale.STATUS_APPROVED)
        )

    def get_supplier_unit_cost_usd(self) -> Decimal:
        return (self.unit_cost or Decimal("0.00")).quantize(Decimal("0.0001"))

    def get_latest_exchange_rate(self) -> Decimal:
        from landing.models import ShipmentItem

        latest_item = (
            ShipmentItem.objects.filter(product=self, shipment__isnull=False)
            .select_related("shipment")
            .order_by("-id")
            .first()
        )
        if latest_item and latest_item.shipment and latest_item.shipment.exchange_rate:
            return Decimal(latest_item.shipment.exchange_rate)
        return Decimal("155.00")

    def get_landed_unit_cost_birr(self) -> Decimal:
        """
        Average landed unit cost for REMAINING stock only.
        This matches your FIFO stock design better than averaging all historical receipts.
        """
        from landing.models import ShipmentItem

        items = ShipmentItem.objects.filter(product=self, quantity_remaining__gt=0)

        if not items.exists():
            return (self.get_supplier_unit_cost_usd() * self.get_latest_exchange_rate()).quantize(Decimal("0.0001"))

        total_remaining_qty = Decimal("0")
        total_remaining_cost_birr = Decimal("0")

        for item in items:
            qty_remaining = Decimal(item.quantity_remaining or 0)
            unit_landed_cost = Decimal(item.unit_landed_cost or 0)

            total_remaining_qty += qty_remaining
            total_remaining_cost_birr += qty_remaining * unit_landed_cost

        if total_remaining_qty <= 0:
            return Decimal("0.0000")

        return (total_remaining_cost_birr / total_remaining_qty).quantize(Decimal("0.0001"))

    def get_suggested_selling_price(self) -> Decimal:
        landed_cost_birr = self.get_landed_unit_cost_birr()
        margin = self.profit_margin_percent or Decimal("0")
        return (landed_cost_birr * (Decimal("1") + margin / Decimal("100"))).quantize(Decimal("0.0001"))

    def get_final_selling_price(self) -> Decimal:
        if self.selling_price is not None:
            return Decimal(self.selling_price).quantize(Decimal("0.0001"))
        return self.get_suggested_selling_price()

    def get_latest_selling_price_birr(self) -> Decimal:
        return self.get_final_selling_price()

    def update_cost_from_shipments(self):
        # Do not overwrite supplier USD unit_cost with ETB landed cost.
        return

    def current_stock_display(self) -> int:
        return self.get_current_stock()
    current_stock_display.short_description = "Current Stock"

    def final_selling_price_display(self) -> Decimal:
        return self.get_final_selling_price()
    final_selling_price_display.short_description = "Final Selling Price (ETB)"

    def latest_selling_price_birr_display(self) -> Decimal:
        return self.get_latest_selling_price_birr()
    latest_selling_price_birr_display.short_description = "Final Selling Price (ETB)"
