from django.db import models
from decimal import Decimal
from products.models import Product
from django.core.exceptions import ValidationError
from landing.models import ShipmentItem

# Default withholding tax percentage (can be overridden per sale)
DEFAULT_WHT_PERCENT = Decimal('2.0')  # 2%

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # editable
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    wht_percent = models.DecimalField(max_digits=5, decimal_places=2, default=DEFAULT_WHT_PERCENT)
    wht_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_vat = models.CharField(max_length=100, blank=True, null=True)
    customer_city = models.CharField(max_length=100, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)

    sale_date = models.DateTimeField(auto_now_add=True)

    # Internal fields to track cost after FIFO consumption
    _unit_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    _cost_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} sold to {self.customer_name or 'Walk-in'}"

    # -------- FIFO STOCK CONSUMPTION --------
    def _consume_fifo_stock(self):
        remaining_qty = self.quantity or 0
        total_cost = Decimal('0.00')

        batches = ShipmentItem.objects.filter(
            product=self.product,
            quantity_remaining__gt=0
        ).order_by('expiry_date')

        for batch in batches:
            if remaining_qty <= 0:
                break

            available = batch.quantity_remaining or 0
            take_qty = min(available, remaining_qty)

            batch.quantity_remaining = available - take_qty
            batch.save(update_fields=['quantity_remaining'])

            unit_cost = batch.unit_landed_cost or Decimal('0.00')
            total_cost += Decimal(take_qty) * unit_cost

            remaining_qty -= take_qty

        if remaining_qty > 0:
            raise ValidationError(
                f"Not enough stock! Available: {self.product.get_current_stock()}, Trying to sell: {self.quantity}"
            )

        self._cost_total = total_cost
        self._unit_cost = (total_cost / self.quantity) if self.quantity > 0 else Decimal('0.00')

    # -------- SAVE METHOD --------
    def save(self, *args, **kwargs):
        # Default unit_price
        if not self.unit_price or self.unit_price == 0:
            if hasattr(self.product, "get_final_selling_price"):
                self.unit_price = self.product.get_final_selling_price()
            else:
                self.unit_price = self.product.selling_price or Decimal('0.00')

        # FIFO stock consumption only on creation
        if not self.pk:
            self._consume_fifo_stock()

        # Calculate WHT
        self.wht_amount = self.get_total() * (self.wht_percent / Decimal('100'))

        super().save(*args, **kwargs)

    # -------- DISPLAY FIELDS --------
    def get_batch_number(self):
        batch = ShipmentItem.objects.filter(
            product=self.product,
            quantity_remaining__gt=0
        ).order_by('expiry_date').first()
        return batch.batch_number if batch else ""
    get_batch_number.short_description = "Batch"

    def get_unit(self):
        return self.product.unit_of_measure if self.product else ""
    get_unit.short_description = "Unit"

    # -------- CALCULATIONS --------
    def get_line_total(self):
        return (self.unit_price or Decimal('0.00')) * (self.quantity or 0)
    get_line_total.short_description = "Line Total"

    def get_discount_amount(self):
        return self.get_line_total() * (self.discount_percent / Decimal('100')) if self.discount_percent else Decimal('0.00')
    get_discount_amount.short_description = "Discount"

    def get_vat_amount(self):
        base = self.get_line_total() - self.get_discount_amount()
        return base * (self.vat_percent / Decimal('100')) if self.vat_percent else Decimal('0.00')
    get_vat_amount.short_description = "VAT"

    def get_total(self):
        return (self.get_line_total() - self.get_discount_amount()) + self.get_vat_amount()
    get_total.short_description = "Total (Incl VAT)"

    def get_wht_amount(self):
        return self.wht_amount or Decimal('0.00')
    get_wht_amount.short_description = "Withholding Tax"

    # -------- PROFIT SYSTEM --------
    def get_cost_price(self):
        return self._unit_cost or Decimal('0.00')
    get_cost_price.short_description = "Cost Price"

    def get_gross_profit(self):
        return (self.get_line_total() - self.get_discount_amount()) - (self.get_cost_price() * (self.quantity or 0))
    get_gross_profit.short_description = "Gross Profit"

    def get_net_profit(self):
        return self.get_gross_profit() - self.get_vat_amount()
    get_net_profit.short_description = "Net Profit"

    def get_margin_percent(self):
        total = self.get_total()
        if total > 0:
            return (self.get_net_profit() / total) * Decimal('100')
        return Decimal('0.00')
    get_margin_percent.short_description = "Margin %"
