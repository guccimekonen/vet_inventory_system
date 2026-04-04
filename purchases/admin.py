from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources, fields
from .models import Purchase
from dashboard.admin import custom_admin_site

class PurchaseResource(resources.ModelResource):
    product_name = fields.Field(column_name='Product Name')
    supplier_name = fields.Field(column_name='Supplier Name')
    total_cost = fields.Field(column_name='Total Cost')

    def dehydrate_product_name(self, purchase):
        return purchase.product.name if purchase.product else ''

    def dehydrate_supplier_name(self, purchase):
        return purchase.supplier.name if purchase.supplier else ''

    def dehydrate_total_cost(self, purchase):
        if hasattr(purchase, 'total_cost') and purchase.total_cost is not None:
            return purchase.total_cost
        return purchase.quantity * purchase.unit_cost if purchase.quantity and purchase.unit_cost else 0

    class Meta:
        model = Purchase
        fields = (
            'product_name', 'supplier_name', 'invoice_number', 'quantity',
            'unit_cost', 'total_cost', 'purchase_date'
        )

class PurchaseAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = PurchaseResource
    list_display = ['product', 'supplier', 'invoice_number', 'quantity', 'unit_cost', 'total_cost', 'purchase_date']
    search_fields = ['invoice_number', 'supplier']
    list_filter = ['purchase_date']

custom_admin_site.register(Purchase, PurchaseAdmin)
