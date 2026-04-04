from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from import_export.admin import ExportMixin
from import_export import resources, fields
from .models import Sale
from decimal import Decimal

# ✅ IMPORTANT: use custom admin
from dashboard.admin import custom_admin_site


# Resource for exporting Sale data with all fields
class SaleResource(resources.ModelResource):
    product_name = fields.Field(column_name='Product Name')
    get_line_total = fields.Field(column_name='Line Total')
    get_discount_amount = fields.Field(column_name='Discount Amount')
    get_vat_amount = fields.Field(column_name='VAT Amount')
    get_total = fields.Field(column_name='Total')
    get_cost_price = fields.Field(column_name='Cost Price')
    get_gross_profit = fields.Field(column_name='Gross Profit')
    get_net_profit = fields.Field(column_name='Net Profit')
    get_margin_percent = fields.Field(column_name='Margin %')
    get_wht_amount = fields.Field(column_name='Withholding Tax')

    def dehydrate_product_name(self, sale):
        return sale.product.name if sale.product else ''

    def dehydrate_get_line_total(self, sale):
        return sale.get_line_total()

    def dehydrate_get_discount_amount(self, sale):
        return sale.get_discount_amount()

    def dehydrate_get_vat_amount(self, sale):
        return sale.get_vat_amount()

    def dehydrate_get_total(self, sale):
        return sale.get_total()

    def dehydrate_get_cost_price(self, sale):
        return sale.get_cost_price()

    def dehydrate_get_gross_profit(self, sale):
        return sale.get_gross_profit()

    def dehydrate_get_net_profit(self, sale):
        return sale.get_net_profit()

    def dehydrate_get_margin_percent(self, sale):
        return sale.get_margin_percent()

    def dehydrate_get_wht_amount(self, sale):
        return (sale.wht_percent / Decimal('100')) * sale.get_total() if sale.wht_percent else Decimal('0.00')

    class Meta:
        model = Sale
        fields = (
            'product_name', 'get_batch_number', 'get_unit', 'quantity', 'unit_price',
            'get_line_total', 'discount_percent', 'get_discount_amount', 'vat_percent',
            'get_vat_amount', 'get_total', 'get_cost_price', 'get_gross_profit',
            'get_net_profit', 'get_margin_percent', 'wht_percent', 'get_wht_amount',
            'sale_date'
        )


# ---------------------- Sale Admin ----------------------
class SaleAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SaleResource

    list_display = (
        'product',
        'get_batch_number',
        'get_unit',
        'quantity',
        'unit_price',
        'get_line_total',
        'discount_percent',
        'get_discount_amount',
        'vat_percent',
        'get_vat_amount',
        'get_total',
        'get_cost_price',
        'get_gross_profit',
        'get_net_profit',
        'get_margin_percent',
        'wht_percent',
        'get_wht_amount',
        'sale_date',
    )

    search_fields = ('product__name', 'product__sku', 'customer_name')
    list_filter = ('sale_date', 'product')

    readonly_fields = (
        'get_line_total',
        'get_discount_amount',
        'get_vat_amount',
        'get_total',
        'get_cost_price',
        'get_gross_profit',
        'get_net_profit',
        'get_margin_percent',
        'get_wht_amount',
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    def get_wht_amount(self, obj):
        return (obj.wht_percent / Decimal('100')) * obj.get_total() if obj.wht_percent else Decimal('0.00')
    get_wht_amount.short_description = "Withholding Tax"


# ✅ IMPORTANT: REGISTER WITH CUSTOM ADMIN
custom_admin_site.register(Sale, SaleAdmin)
