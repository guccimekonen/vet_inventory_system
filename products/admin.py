from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources, fields
from .models import Product
from dashboard.admin import custom_admin_site  # ensure using your custom admin

# ---------------------- Resource ----------------------
class ProductResource(resources.ModelResource):
    get_final_selling_price = fields.Field(column_name='Selling Price ($)')
    get_selling_price_birr = fields.Field(column_name='Selling Price (ETB)')
    get_current_stock = fields.Field(column_name='Current Stock')
    get_suggested_selling_price = fields.Field(column_name='Suggested Selling Price')

    def dehydrate_get_final_selling_price(self, product):
        return product.get_final_selling_price() if hasattr(product, 'get_final_selling_price') else 0

    def dehydrate_get_selling_price_birr(self, product):
        return product.get_latest_selling_price_birr() if hasattr(product, 'get_latest_selling_price_birr') else 0

    def dehydrate_get_current_stock(self, product):
        return product.get_current_stock() if hasattr(product, 'get_current_stock') else 0

    def dehydrate_get_suggested_selling_price(self, product):
        return product.get_suggested_selling_price() if hasattr(product, 'get_suggested_selling_price') else 0

    class Meta:
        model = Product
        fields = (
            'sku', 'name', 'batch_number', 'unit_of_measure', 'unit_cost',
            'get_suggested_selling_price', 'get_final_selling_price', 'get_selling_price_birr',
            'profit_margin_percent', 'reorder_level', 'get_current_stock', 'controlled', 'created_at'
        )

# ---------------------- Admin ----------------------
@admin.register(Product)
class ProductAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ProductResource

    list_display = (
        'sku', 'name', 'batch_number', 'unit_of_measure', 'unit_cost',
        'get_final_selling_price', 'get_latest_selling_price_birr',
        'profit_margin_percent', 'reorder_level', 'get_current_stock', 'controlled', 'created_at',
    )

    readonly_fields = (
        'get_current_stock',
        'get_suggested_selling_price',
        'get_final_selling_price',
        'get_latest_selling_price_birr',
    )

    fieldsets = (
        ("Basic Info", {'fields': ('sku', 'name', 'description', 'unit_of_measure', 'batch_number')}),
        ("Cost & Pricing", {'fields': ('unit_cost', 'selling_price', 'profit_margin_percent')}),
        ("Stock", {'fields': ('reorder_level', 'opening_quantity', 'get_current_stock')}),
        ("Control", {'fields': ('hs_code', 'controlled')}),
    )

    def get_suggested_selling_price(self, obj):
        return obj.get_suggested_selling_price()
    get_suggested_selling_price.short_description = "Suggested Selling Price"

    def get_final_selling_price(self, obj):
        return obj.get_final_selling_price()
    get_final_selling_price.short_description = "Selling Price ($)"

    def get_latest_selling_price_birr(self, obj):
        if hasattr(obj, 'get_latest_selling_price_birr'):
            return obj.get_latest_selling_price_birr()
        return 0
    get_latest_selling_price_birr.short_description = "Selling Price (ETB)"

    def get_current_stock(self, obj):
        return obj.get_current_stock()
    get_current_stock.short_description = "Current Stock"

# ---------------------- Register with custom admin ----------------------
custom_admin_site.register(Product, ProductAdmin)
