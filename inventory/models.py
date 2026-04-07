from django.db import models
from decimal import Decimal
from products.models import Product

# =========================
# STOCK LEDGER ENTRY
# =========================
class StockLedger(models.Model):
    MOVEMENT_CHOICES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    movement_type = models.CharField(max_length=3, choices=MOVEMENT_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    # ✅ FIX: ensure never NULL and always has value
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal('0.00')
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    reference = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} | {self.movement_type} | Qty: {self.quantity}"

    def save(self, *args, **kwargs):
        # ✅ SAFETY: if unit_cost is None → set to 0
        if self.unit_cost is None:
            self.unit_cost = Decimal('0.00')

        # ✅ SAFETY: if quantity is None → set to 0
        if self.quantity is None:
            self.quantity = Decimal('0.00')

        # ✅ AUTO CALCULATE TOTAL COST
        self.total_cost = self.quantity * self.unit_cost

        super().save(*args, **kwargs)
