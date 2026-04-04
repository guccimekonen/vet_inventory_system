from django.db.models.signals import post_save
from django.dispatch import receiver
from sales.models import Sale
from .models import VATReport
from decimal import Decimal

@receiver(post_save, sender=Sale)
def update_vat_report(sender, instance, created, **kwargs):
    """
    Automatically update the monthly VAT report whenever a Sale is created.
    """
    if created:
        # Calculate VAT collected for this sale
        vat_amount = instance.get_vat_amount() or Decimal('0.00')
        wht_amount = getattr(instance, 'wht_amount', Decimal('0.00'))

        # Get or create a VAT report for the same month/year
        report, _ = VATReport.objects.get_or_create(
            year=instance.sale_date.year,
            month=instance.sale_date.month
        )

        # Update totals
        report.total_vat_collected += vat_amount
        report.total_wht_deducted += wht_amount
        report.save()
        
