from django.db import models
from decimal import Decimal

# =========================
# PRODUCT MODEL
# =========================
class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    unit_of_measure = models.CharField(max_length=50)

    # ✅ OPTIONAL (legacy, not used for FIFO anymore)
    batch_number = models.CharField(max_length=100, blank=True, null=True)

    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ MANUAL SELLING PRICE (you can override)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # ✅ PROFIT MARGIN %
    profit_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    reorder_level = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    hs_code = models.CharField(max_length=50, blank=True, null=True)
    controlled = models.BooleanField(default=False)

    # ⚠️ Legacy (no longer used for stock calculation)
    opening_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    # -------------------------
    # STOCK CALCULATIONS (SINGLE SOURCE OF TRUTH)
    # -------------------------
    def get_current_stock(self):
        from landing.models import ShipmentItem
        return sum(item.quantity_remaining or 0 for item in ShipmentItem.objects.filter(product=self))

    # -------------------------
    # OPTIONAL (LEGACY - FINANCIAL PURPOSE ONLY)
    # -------------------------
    def get_total_purchased(self):
        return sum(p.quantity or 0 for p in self.purchase_set.all())

    def get_total_sold(self):
        from sales.models import Sale
        return sum(s.quantity or 0 for s in Sale.objects.filter(product=self))

    # -------------------------
    # LANDING COST UPDATE
    # -------------------------
    def update_cost_from_shipments(self):
        from landing.models import ShipmentItem
        items = ShipmentItem.objects.filter(product=self)
        total_qty = sum(item.quantity or 0 for item in items)
        total_value = sum(item.total_cost or 0 for item in items)

        if total_qty > 0:
            self.unit_cost = total_value / total_qty
            self.save()

    # -------------------------
    # SELLING PRICE SYSTEM
    # -------------------------
    def get_suggested_selling_price(self):
        if self.unit_cost:
            margin = self.profit_margin_percent or Decimal('0')
            return self.unit_cost * (1 + (margin / Decimal('100')))
        return Decimal('0.00')

    def get_final_selling_price(self):
        return self.selling_price or self.get_suggested_selling_price()

    # -------------------------
    # SELLING PRICE IN BIRR (ETB)
    # -------------------------
    def get_latest_selling_price_birr(self):
        """
        Returns weighted average selling price in ETB across all shipment items.
        Applies profit margin only once and avoids double multiplication.
        """
        from landing.models import ShipmentItem
        items = ShipmentItem.objects.filter(product=self)
        if not items.exists():
            # fallback: suggested price in USD
            return self.get_suggested_selling_price()

        total_qty = Decimal('0')
        total_value_birr = Decimal('0')

        for item in items:
            qty = Decimal(item.quantity or 0)
            unit_cost = Decimal(item.unit_landed_cost or 0)
            exchange_rate = Decimal(item.shipment.exchange_rate or 1) if item.shipment else Decimal('1.00')

            total_qty += qty
            total_value_birr += unit_cost * exchange_rate * qty

        if total_qty > 0:
            avg_price_birr = total_value_birr / total_qty

            # Apply profit margin only if no manual selling price
            if self.selling_price is None:
                margin = self.profit_margin_percent or Decimal('0')
                avg_price_birr = avg_price_birr * (1 + margin / Decimal('100'))
        else:
            avg_price_birr = Decimal('0.00')

        # If manual selling price exists, use it × latest shipment exchange rate
        if self.selling_price is not None:
            latest_item = items.order_by('-id').first()
            exchange_rate = Decimal(latest_item.shipment.exchange_rate or 1) if latest_item.shipment else Decimal('1.00')
            avg_price_birr = self.selling_price * exchange_rate

        return avg_price_birr.quantize(Decimal('0.0001'))

    # -------------------------
    # ADMIN-FRIENDLY DISPLAY FIELDS
    # -------------------------
    def current_stock_display(self):
        return self.get_current_stock()
    current_stock_display.short_description = "Current Stock"

    def final_selling_price_display(self):
        return self.get_final_selling_price()
    final_selling_price_display.short_description = "Selling Price"

    def latest_selling_price_birr_display(self):
        return self.get_latest_selling_price_birr()
    latest_selling_price_birr_display.short_description = "Selling Price (ETB)"
