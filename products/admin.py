from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources, fields

from .models import Product
from dashboard.admin import custom_admin_site


class ProductResource(resources.ModelResource):
    supplier_unit_cost_usd = fields.Field(column_name="Unit Cost ($)")
    landed_unit_cost_etb = fields.Field(column_name="Landed Cost (ETB)")
    suggested_selling_price_etb = fields.Field(column_name="Suggested Selling Price (ETB)")
    final_selling_price_etb = fields.Field(column_name="Final Selling Price (ETB)")
    current_stock = fields.Field(column_name="Current Stock")

    def dehydrate_supplier_unit_cost_usd(self, product):
        return product.get_supplier_unit_cost_usd()

    def dehydrate_landed_unit_cost_etb(self, product):
        return product.get_landed_unit_cost_birr()

    def dehydrate_suggested_selling_price_etb(self, product):
        return product.get_suggested_selling_price()

    def dehydrate_final_selling_price_etb(self, product):
        return product.get_final_selling_price()

    def dehydrate_current_stock(self, product):
        return product.get_current_stock()

    class Meta:
        model = Product
        fields = (
            "sku",
            "name",
            "batch_number",
            "unit_of_measure",
            "supplier_unit_cost_usd",
            "landed_unit_cost_etb",
            "suggested_selling_price_etb",
            "final_selling_price_etb",
            "profit_margin_percent",
            "reorder_level",
            "current_stock",
            "controlled",
            "created_at",
        )


class ProductAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ProductResource

    list_display = (
        "sku",
        "name",
        "batch_number",
        "unit_of_measure",
        "get_supplier_unit_cost_usd",
        "get_landed_unit_cost_birr",
        "get_suggested_selling_price_etb",
        "get_final_selling_price_etb",
        "profit_margin_percent",
        "reorder_level",
        "get_current_stock",
        "controlled",
        "created_at",
    )

    readonly_fields = (
        "get_current_stock",
        "get_landed_unit_cost_birr",
        "get_suggested_selling_price_etb",
        "get_final_selling_price_etb",
    )

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "sku",
                    "name",
                    "description",
                    "unit_of_measure",
                    "batch_number",
                )
            },
        ),
        (
            "Cost & Pricing",
            {
                "fields": (
                    "unit_cost",
                    "profit_margin_percent",
                    "get_landed_unit_cost_birr",
                    "get_suggested_selling_price_etb",
                    "selling_price",
                    "get_final_selling_price_etb",
                )
            },
        ),
        (
            "Stock",
            {
                "fields": (
                    "reorder_level",
                    "opening_quantity",
                    "get_current_stock",
                )
            },
        ),
        (
            "Control",
            {
                "fields": (
                    "hs_code",
                    "controlled",
                )
            },
        ),
    )

    def get_supplier_unit_cost_usd(self, obj):
        return obj.get_supplier_unit_cost_usd()
    get_supplier_unit_cost_usd.short_description = "Unit Cost ($)"

    def get_landed_unit_cost_birr(self, obj):
        return obj.get_landed_unit_cost_birr()
    get_landed_unit_cost_birr.short_description = "Landed Cost (ETB)"

    def get_suggested_selling_price_etb(self, obj):
        return obj.get_suggested_selling_price()
    get_suggested_selling_price_etb.short_description = "Suggested Selling Price (ETB)"

    def get_final_selling_price_etb(self, obj):
        return obj.get_final_selling_price()
    get_final_selling_price_etb.short_description = "Final Selling Price (ETB)"

    def get_current_stock(self, obj):
        return obj.get_current_stock()
    get_current_stock.short_description = "Current Stock"


try:
    admin.site.unregister(Product)
except admin.sites.NotRegistered:
    pass

admin.site.register(Product, ProductAdmin)

try:
    custom_admin_site.unregister(Product)
except admin.sites.NotRegistered:
    pass

custom_admin_site.register(Product, ProductAdmin)
