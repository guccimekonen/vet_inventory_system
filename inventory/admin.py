from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources, fields
from .models import StockLedger
from decimal import Decimal
from dashboard.admin import custom_admin_site  # use your custom admin

# ---------------------- StockLedger Resource ----------------------
class StockLedgerResource(resources.ModelResource):
    product_name = fields.Field(column_name='Product Name')
    total_cost = fields.Field(column_name='Total Cost')

    def dehydrate_product_name(self, obj):
        return obj.product.name if obj.product else ''

    def dehydrate_total_cost(self, obj):
        return (obj.unit_cost or Decimal('0.00')) * (obj.quantity or 0)

    class Meta:
        model = StockLedger
        fields = (
            'product_name', 'batch_number', 'expiry_date',
            'movement_type', 'quantity', 'unit_cost', 'total_cost', 'reference', 'created_at'
        )


# ---------------------- Admin ----------------------
@admin.register(StockLedger)
class StockLedgerAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = StockLedgerResource

    list_display = (
        'product', 'batch_number', 'expiry_date',
        'movement_type', 'quantity', 'unit_cost', 'total_cost', 'reference', 'created_at'
    )
    list_filter = ('movement_type', 'product')
    search_fields = ('product__name', 'batch_number', 'reference')
    readonly_fields = ('total_cost', 'created_at')

    def total_cost(self, obj):
        """
        Calculate total cost dynamically if not stored
        """
        return (obj.unit_cost or Decimal('0.00')) * (obj.quantity or 0)
    total_cost.short_description = 'Total Cost'

# ---------------------- Register with custom admin ----------------------
custom_admin_site.register(StockLedger, StockLedgerAdmin)
