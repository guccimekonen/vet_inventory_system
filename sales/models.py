from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from products.models import Product
from landing.models import ShipmentItem


DEFAULT_WHT_PERCENT = Decimal("2.0")
WHT_THRESHOLD_ETB = Decimal("10000.00")
User = get_user_model()


class Sale(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # ETB
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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sales_requested",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sales_approved",
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    stock_applied = models.BooleanField(default=False)

    _unit_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    _cost_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    consumed_batch_number = models.CharField(max_length=100, blank=True, null=True)
    consumed_expiry_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-sale_date"]

    def __str__(self):
        return f"{self.product.name} - {self.quantity} for {self.customer_name or 'Walk-in'} [{self.status}]"

    def _consume_fifo_stock(self):
        remaining_qty = self.quantity or 0
        total_cost = Decimal("0.00")
        first_batch_number = None
        first_expiry_date = None

        batches = ShipmentItem.objects.filter(
            product=self.product,
            quantity_remaining__gt=0
        ).order_by("expiry_date", "id")

        for batch in batches:
            if remaining_qty <= 0:
                break

            available = batch.quantity_remaining or 0
            take_qty = min(available, remaining_qty)

            if first_batch_number is None:
                first_batch_number = batch.batch_number
                first_expiry_date = batch.expiry_date

            batch.quantity_remaining = available - take_qty
            batch.save(update_fields=["quantity_remaining"])

            unit_cost = batch.unit_landed_cost or Decimal("0.00")
            total_cost += Decimal(take_qty) * unit_cost

            remaining_qty -= take_qty

        if remaining_qty > 0:
            raise ValidationError(
                f"Not enough stock! Available: {self.product.get_current_stock()}, Trying to sell: {self.quantity}"
            )

        self._cost_total = total_cost
        self._unit_cost = (total_cost / self.quantity) if self.quantity > 0 else Decimal("0.00")
        self.consumed_batch_number = first_batch_number
        self.consumed_expiry_date = first_expiry_date

    def approve(self, user=None):
        if self.stock_applied and self.status == self.STATUS_APPROVED:
            return

        self._consume_fifo_stock()
        self.status = self.STATUS_APPROVED
        self.stock_applied = True
        self.approved_at = timezone.now()
        self.rejection_reason = ""

        if user is not None and getattr(user, "is_authenticated", False):
            self.approved_by = user

        self.wht_amount = self.calculate_wht_amount()

        self.save(update_fields=[
            "status",
            "stock_applied",
            "approved_at",
            "approved_by",
            "rejection_reason",
            "_cost_total",
            "_unit_cost",
            "consumed_batch_number",
            "consumed_expiry_date",
            "wht_amount",
        ])

    def reject(self, user=None, reason=""):
        if self.stock_applied:
            raise ValidationError("Approved sales cannot be rejected directly. Create a return/adjustment workflow instead.")

        self.status = self.STATUS_REJECTED
        self.approved_at = timezone.now()

        if user is not None and getattr(user, "is_authenticated", False):
            self.approved_by = user

        self.rejection_reason = reason or self.rejection_reason or ""
        self.save(update_fields=[
            "status",
            "approved_at",
            "approved_by",
            "rejection_reason",
        ])

    def save(self, *args, **kwargs):
        if not self.unit_price or self.unit_price == 0:
            if hasattr(self.product, "get_final_selling_price"):
                self.unit_price = self.product.get_final_selling_price()
            else:
                self.unit_price = self.product.selling_price or Decimal("0.00")

        self.wht_amount = self.calculate_wht_amount()
        super().save(*args, **kwargs)

    def get_batch_number(self):
        return self.consumed_batch_number or ""
    get_batch_number.short_description = "Batch"

    def get_unit(self):
        return self.product.unit_of_measure if self.product else ""
    get_unit.short_description = "Unit"

    def get_line_total(self):
        return (self.unit_price or Decimal("0.00")) * (self.quantity or 0)
    get_line_total.short_description = "Line Total"

    def get_discount_amount(self):
        if not self.discount_percent:
            return Decimal("0.00")
        return self.get_line_total() * (self.discount_percent / Decimal("100"))
    get_discount_amount.short_description = "Discount"

    def get_before_vat_total(self):
        return self.get_line_total() - self.get_discount_amount()
    get_before_vat_total.short_description = "Before VAT"

    def get_vat_amount(self):
        base = self.get_before_vat_total()
        return base * (self.vat_percent / Decimal("100")) if self.vat_percent else Decimal("0.00")
    get_vat_amount.short_description = "VAT"

    def get_total(self):
        return self.get_before_vat_total() + self.get_vat_amount()
    get_total.short_description = "Total (Incl VAT)"

    def calculate_wht_amount(self):
        before_vat_total = self.get_before_vat_total()
        if before_vat_total > WHT_THRESHOLD_ETB:
            return before_vat_total * ((self.wht_percent or Decimal("0.00")) / Decimal("100"))
        return Decimal("0.00")

    def get_wht_amount(self):
        return self.wht_amount or Decimal("0.00")
    get_wht_amount.short_description = "Withholding Tax"

    def get_net_payable(self):
        return self.get_total() - self.get_wht_amount()
    get_net_payable.short_description = "Net Payable"

    def get_cost_price(self):
        return self._unit_cost or Decimal("0.00")
    get_cost_price.short_description = "Cost Price"

    def get_gross_profit(self):
        return self.get_before_vat_total() - (self.get_cost_price() * (self.quantity or 0))
    get_gross_profit.short_description = "Gross Profit"

    def get_net_profit(self):
        return self.get_gross_profit() - self.get_vat_amount()
    get_net_profit.short_description = "Net Profit"

    def get_margin_percent(self):
        total = self.get_total()
        if total > 0:
            return (self.get_net_profit() / total) * Decimal("100")
        return Decimal("0.00")
    get_margin_percent.short_description = "Margin %"
