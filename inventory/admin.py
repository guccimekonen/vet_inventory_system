from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ExportMixin
from import_export import resources, fields

from .models import StockLedger
from dashboard.admin import custom_admin_site


class StockLedgerResource(resources.ModelResource):
    product_name = fields.Field(column_name="Product Name")
    total_cost_value = fields.Field(column_name="Total Cost (ETB)")

    def dehydrate_product_name(self, obj):
        return obj.product.name if obj.product else ""

    def dehydrate_total_cost_value(self, obj):
        return (obj.unit_cost or Decimal("0.00")) * (obj.quantity or 0)

    class Meta:
        model = StockLedger
        fields = (
            "product_name",
            "batch_number",
            "expiry_date",
            "movement_type",
            "quantity",
            "unit_cost",
            "total_cost_value",
            "reference",
            "created_at",
        )


class StockLedgerAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = StockLedgerResource

    list_display = (
        "compact_product",
        "batch_number",
        "expiry_date",
        "movement_type",
        "quantity",
        "unit_cost_display",
        "total_cost_display",
        "reference",
        "created_at",
    )
    list_filter = ("movement_type", "product")
    search_fields = ("product__name", "batch_number", "reference")
    readonly_fields = ("total_cost", "created_at")

    @admin.display(description="Product", ordering="product__sku")
    def compact_product(self, obj):
        if not obj.product:
            return "-"

        return format_html(
            '<div class="compact-product-cell"><strong>{}</strong><br><span>{}</span></div>',
            obj.product.sku or "-",
            obj.product.name or "-",
        )

    def unit_cost_display(self, obj):
        return obj.unit_cost or Decimal("0.00")
    unit_cost_display.short_description = "Unit Cost (ETB)"

    def total_cost_display(self, obj):
        return (obj.unit_cost or Decimal("0.00")) * (obj.quantity or 0)
    total_cost_display.short_description = "Total Cost (ETB)"


try:
    custom_admin_site.unregister(StockLedger)
except admin.sites.NotRegistered:
    pass

custom_admin_site.register(StockLedger, StockLedgerAdmin)
