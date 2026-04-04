from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, F, FloatField, Case, When

from products.models import Product
from sales.models import Sale
from inventory.models import StockLedger
from landing.models import Shipment


def dashboard_view(request):
    sales = Sale.objects.select_related("product").all()
    products = Product.objects.all()

    # KPI calculations
    total_sales = Decimal("0.00")
    total_vat = Decimal("0.00")
    gross_profit = Decimal("0.00")

    for sale in sales:
        total_sales += sale.get_line_total() or Decimal("0.00")
        total_vat += sale.get_vat_amount() or Decimal("0.00")

        try:
            gross_profit += sale.get_profit() or Decimal("0.00")
        except AttributeError:
            pass
        except TypeError:
            pass

    net_profit = gross_profit - total_vat

    # Stock summary by product
    stock_summary_qs = StockLedger.objects.values("product").annotate(
        qty_in=Sum(
            Case(
                When(movement_type="IN", then=F("quantity")),
                default=0,
                output_field=FloatField(),
            )
        ),
        qty_out=Sum(
            Case(
                When(movement_type="OUT", then=F("quantity")),
                default=0,
                output_field=FloatField(),
            )
        ),
    )

    stock_summary = {
        item["product"]: {
            "qty_in": item["qty_in"] or 0,
            "qty_out": item["qty_out"] or 0,
        }
        for item in stock_summary_qs
    }

    total_stock_value = Decimal("0.00")
    low_stock_products = []

    for product in products:
        summary = stock_summary.get(product.id, {"qty_in": 0, "qty_out": 0})
        current_qty = summary["qty_in"] - summary["qty_out"]

        latest_entry = (
            StockLedger.objects.filter(product=product)
            .order_by("-created_at")
            .first()
        )

        unit_cost = (
            latest_entry.unit_cost
            if latest_entry and latest_entry.unit_cost
            else Decimal("0.00")
        )

        total_stock_value += Decimal(str(current_qty)) * unit_cost

        reorder_level = product.reorder_level or 0
        if current_qty <= reorder_level:
            low_stock_products.append(
                {
                    "product": product,
                    "current_qty": round(current_qty, 2),
                }
            )

    # Expiry alerts
    expiry_limit = timezone.now().date() + timedelta(days=180)
    expiry_alerts = (
        StockLedger.objects.select_related("product")
        .filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_limit,
        )
        .order_by("expiry_date")
    )

    # Top selling products
    top_products = (
        Sale.objects.values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:10]
    )

    chart_labels = [item["product__name"] or "Unnamed Product" for item in top_products]
    chart_data = [float(item["total_qty"] or 0) for item in top_products]

    # Sales forecast
    last_30_sales = list(Sale.objects.order_by("-sale_date")[:30])[::-1]
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
    sales = Sale.objects.all()
    shipments = Shipment.objects.all()

    output_vat = sum((sale.get_vat_amount() or Decimal("0.00")) for sale in sales)
    input_vat = sum((shipment.custom_duty_tax or Decimal("0.00")) for shipment in shipments)
    vat_payable = output_vat - input_vat

    context = {
        "output_vat": round(output_vat, 2),
        "input_vat": round(input_vat, 2),
        "vat_payable": round(vat_payable, 2),
        "sales": sales,
        "shipments": shipments,
    }

    return render(request, "dashboard/vat_report.html", context)
