from decimal import Decimal
from datetime import timedelta

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from landing.models import Shipment, ShipmentItem
from products.models import Product
from sales.models import Sale


def dashboard_view(request):
    sales = Sale.objects.filter(status=Sale.STATUS_APPROVED).select_related("product")
    products = Product.objects.all()

    total_sales = sum((sale.get_line_total() or Decimal("0.00")) for sale in sales)
    total_vat = sum((sale.get_vat_amount() or Decimal("0.00")) for sale in sales)
    gross_profit = sum((sale.get_gross_profit() or Decimal("0.00")) for sale in sales)
    net_profit = sum((sale.get_net_profit() or Decimal("0.00")) for sale in sales)

    total_stock_value = sum(
        (Decimal(item.quantity_remaining or 0) * Decimal(item.unit_landed_cost or 0))
        for item in ShipmentItem.objects.filter(quantity_remaining__gt=0)
    )

    low_stock_products = []
    for product in products:
        current_qty = product.get_current_stock()
        reorder_level = product.reorder_level or 0

        if current_qty <= reorder_level:
            low_stock_products.append(
                {
                    "product": product,
                    "current_qty": round(current_qty, 2),
                }
            )

    expiry_limit = timezone.now().date() + timedelta(days=180)
    expiry_alerts = (
        ShipmentItem.objects.select_related("product")
        .filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_limit,
            quantity_remaining__gt=0,
        )
        .order_by("expiry_date")
    )

    top_products = (
        Sale.objects.filter(status=Sale.STATUS_APPROVED)
        .values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:10]
    )

    chart_labels = [item["product__name"] or "Unnamed Product" for item in top_products]
    chart_data = [float(item["total_qty"] or 0) for item in top_products]

    last_30_sales = list(
        Sale.objects.filter(status=Sale.STATUS_APPROVED).order_by("-sale_date")[:30]
    )[::-1]
    sales_forecast = []

    for index, sale in enumerate(last_30_sales):
        subset = last_30_sales[max(0, index - 6): index + 1]
        avg = sum(item.quantity or 0 for item in subset) / len(subset) if subset else 0

        sales_forecast.append(
            {
                "date": sale.sale_date.strftime("%Y-%m-%d"),
                "moving_avg": round(avg, 2),
            }
        )

    context = {
        "total_sales": round(total_sales, 2),
        "gross_profit": round(gross_profit, 2),
        "net_profit": round(net_profit, 2),
        "total_vat": round(total_vat, 2),
        "total_stock_value": round(total_stock_value, 2),
        "low_stock_products": low_stock_products,
        "expiry_alerts": expiry_alerts,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "sales_forecast": sales_forecast,
    }

    return render(request, "dashboard/dashboard.html", context)


def vat_report_view(request):
    sales = Sale.objects.filter(status=Sale.STATUS_APPROVED)
    shipments = Shipment.objects.all()

    output_vat = sum((sale.get_vat_amount() or Decimal("0.00")) for sale in sales)

    input_vat = Decimal("0.00")
    vat_payable = output_vat - input_vat

    context = {
        "output_vat": round(output_vat, 2),
        "input_vat": round(input_vat, 2),
        "vat_payable": round(vat_payable, 2),
        "sales": sales,
        "shipments": shipments,
    }

    return render(request, "dashboard/vat_report.html", context)
