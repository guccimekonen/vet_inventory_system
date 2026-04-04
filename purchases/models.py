from django.db import models
from django.utils import timezone
from products.models import Product


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True)

    purchase_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | {self.invoice_number}"
