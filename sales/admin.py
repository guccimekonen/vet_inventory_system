from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from import_export.admin import ExportMixin
from import_export import resources, fields

from .models import Sale
from dashboard.admin import custom_admin_site


class SaleResource(resources.ModelResource):
    product_name = fields.Field(column_name="Product Name")
    before_vat_total = fields.Field(column_name="Before VAT")
    line_total_value = fields.Field(column_name="Line Total")
    discount_amount_value = fields.Field(column_name="Discount Amount")
    vat_amount_value = fields.Field(column_name="VAT Amount")
    total_value = fields.Field(column_name="Total (Incl VAT)")
    wht_amount_value = fields.Field(column_name="Withholding Tax")
    net_payable_value = fields.Field(column_name="Net Payable")
    cost_price_value = fields.Field(column_name="Cost Price")
    gross_profit_value = fields.Field(column_name="Gross Profit")
    net_profit_value = fields.Field(column_name="Net Profit")
    margin_percent_value = fields.Field(column_name="Margin %")

    def dehydrate_product_name(self, sale):
        return sale.product.name if sale.product else ""

    def dehydrate_before_vat_total(self, sale):
        return sale.get_before_vat_total()

    def dehydrate_line_total_value(self, sale):
        return sale.get_line_total()

    def dehydrate_discount_amount_value(self, sale):
        return sale.get_discount_amount()

    def dehydrate_vat_amount_value(self, sale):
        return sale.get_vat_amount()

    def dehydrate_total_value(self, sale):
        return sale.get_total()

    def dehydrate_wht_amount_value(self, sale):
        return sale.get_wht_amount()

    def dehydrate_net_payable_value(self, sale):
        return sale.get_net_payable()

    def dehydrate_cost_price_value(self, sale):
        return sale.get_cost_price()

    def dehydrate_gross_profit_value(self, sale):
        return sale.get_gross_profit()

    def dehydrate_net_profit_value(self, sale):
        return sale.get_net_profit()

    def dehydrate_margin_percent_value(self, sale):
        return sale.get_margin_percent()

    class Meta:
        model = Sale
        fields = (
            "product_name",
            "get_batch_number",
            "get_unit",
            "quantity",
            "unit_price",
            "line_total_value",
            "discount_percent",
            "discount_amount_value",
            "before_vat_total",
            "vat_percent",
            "vat_amount_value",
            "total_value",
            "wht_percent",
            "wht_amount_value",
            "net_payable_value",
            "cost_price_value",
            "gross_profit_value",
            "net_profit_value",
            "margin_percent_value",
            "sale_date",
        )


class SaleAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SaleResource

    list_display = (
        "product",
        "get_batch_number",
        "get_unit",
        "quantity",
        "unit_price",
        "get_line_total",
        "discount_percent",
        "get_discount_amount",
        "get_before_vat_total",
        "vat_percent",
        "get_vat_amount",
        "get_total",
        "wht_percent",
        "get_wht_amount",
        "get_net_payable",
        "get_cost_price",
        "get_gross_profit",
        "get_net_profit",
        "get_margin_percent",
        "sale_date",
    )

    search_fields = ("product__name", "product__sku", "customer_name")
    list_filter = ("sale_date", "product")

    readonly_fields = (
        "get_line_total",
        "get_discount_amount",
        "get_before_vat_total",
        "get_vat_amount",
        "get_total",
        "get_wht_amount",
        "get_net_payable",
        "get_cost_price",
        "get_gross_profit",
        "get_net_profit",
        "get_margin_percent",
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    def get_wht_amount(self, obj):
        return obj.get_wht_amount()
    get_wht_amount.short_description = "Withholding Tax"

    def get_net_payable(self, obj):
        return obj.get_net_payable()
    get_net_payable.short_description = "Net Payable"


try:
    custom_admin_site.unregister(Sale)
except admin.sites.NotRegistered:
    pass

custom_admin_site.register(Sale, SaleAdmin)
