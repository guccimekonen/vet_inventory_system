from decimal import Decimal

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from sales.models import Sale
from .models import VATReport


def recalculate_monthly_vat_report(year, month):
    sales = Sale.objects.filter(
        sale_date__year=year,
        sale_date__month=month,
        status=Sale.STATUS_APPROVED,
    )

    total_vat = sum((sale.get_vat_amount() or Decimal("0.00")) for sale in sales)
    total_wht = sum((sale.get_wht_amount() or Decimal("0.00")) for sale in sales)

    report, _ = VATReport.objects.get_or_create(year=year, month=month)
    report.total_vat_collected = total_vat
    report.total_wht_deducted = total_wht
    report.save()


@receiver(post_save, sender=Sale)
def update_vat_report_on_sale_save(sender, instance, **kwargs):
    recalculate_monthly_vat_report(instance.sale_date.year, instance.sale_date.month)


@receiver(post_delete, sender=Sale)
def update_vat_report_on_sale_delete(sender, instance, **kwargs):
    recalculate_monthly_vat_report(instance.sale_date.year, instance.sale_date.month)

