from django.db import models
from decimal import Decimal

class VATReport(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()

    total_vat_collected = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total_wht_deducted = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'month')  # ✅ prevents duplicate months
        ordering = ['-year', '-month']

    def __str__(self):
        return f"VAT Report - {self.month:02d}/{self.year}"
