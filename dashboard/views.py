from decimal import Decimal
from datetime import timedelta

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from landing.models import Shipment, ShipmentItem
from products.models import Product
from sales.models import Sale


PROFIT_TAX_PERCENT = Decimal("30.00")  # Change this anytime manually


def dashboard_view(request):
    sales = Sale.objects.filter(status=Sale.STATUS_APPROVED).select_related("product")
    products = Product.objects.all()
    shipments = Shipment.objects.all()
    shipment_items = ShipmentItem.objects.select_related("product", "shipment").all()

    total_sales = sum((sale.get_line_total() or Decimal("0.00")) for sale in sales)
    total_vat = sum((sale.get_vat_amount() or Decimal("0.00")) for sale in sales)
    gross_profit = sum((sale.get_gross_profit() or Decimal("0.00")) for sale in sales)
    net_profit = sum((sale.get_net_profit() or Decimal("0.00")) for sale in sales)

    total_stock_value = sum(
        (Decimal(item.quantity_remaining or 0) * Decimal(item.unit_landed_cost or 0))
        for item in ShipmentItem.objects.filter(quantity_remaining__gt=0)
    )

    # Projected Import Profit
    # Uses ordered/imported quantity, not current remaining stock.
    projected_sales_value = sum(
        Decimal(item.quantity or 0) * Decimal(item.product.get_suggested_selling_price() or 0)
        for item in shipment_items
    )

    total_import_cost = sum(
        (Decimal(shipment.get_total_fob_birr() or 0) + Decimal(shipment.total_additional_cost or 0))
        for shipment in shipments
    )

    projected_profit_before_tax = projected_sales_value - total_import_cost

    if projected_sales_value > 0:
        projected_profit_percent = (
            (projected_profit_before_tax / projected_sales_value) * Decimal("100")
        )
    else:
        projected_profit_percent = Decimal("0.00")

    taxable_profit = projected_profit_before_tax if projected_profit_before_tax > 0 else Decimal("0.00")
    profit_tax_payable = taxable_profit * (PROFIT_TAX_PERCENT / Decimal("100"))
    projected_profit_after_tax = projected_profit_before_tax - profit_tax_payable

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

        "projected_sales_value": round(projected_sales_value, 2),
        "total_import_cost": round(total_import_cost, 2),
        "projected_profit_before_tax": round(projected_profit_before_tax, 2),
        "projected_profit_percent": round(projected_profit_percent, 2),
        "profit_tax_percent": round(PROFIT_TAX_PERCENT, 2),
        "profit_tax_payable": round(profit_tax_payable, 2),
        "projected_profit_after_tax": round(projected_profit_after_tax, 2),

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
