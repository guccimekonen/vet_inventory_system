from django.contrib import admin
from import_export.admin import ExportMixin
from import_export import resources, fields
from .models import Shipment, ShipmentItem
from decimal import Decimal

# ✅ IMPORTANT: use custom admin
from dashboard.admin import custom_admin_site


# ---------------------- ShipmentItem Resource ----------------------
class ShipmentItemResource(resources.ModelResource):
    shipment_ref = fields.Field(column_name='Shipment Reference')
    product_name = fields.Field(column_name='Product Name')

    fob_usd = fields.Field(column_name='FOB USD')
    fob_birr = fields.Field(column_name='FOB ETB')
    unit_price_birr = fields.Field(column_name='Unit Price ETB')

    allocated_cost = fields.Field(column_name='Allocated Cost')
    total_cost = fields.Field(column_name='Total Cost')
    unit_landed_cost = fields.Field(column_name='Unit Landed Cost')
    suggested_price = fields.Field(column_name='Suggested Selling Price ETB')
    quantity_remaining = fields.Field(column_name='Quantity Remaining')

    def dehydrate_shipment_ref(self, item):
        return item.shipment.reference if item.shipment else ''

    def dehydrate_product_name(self, item):
        return item.product.name if item.product else ''

    def dehydrate_fob_usd(self, item):
        return item.get_fob_value()

    def dehydrate_fob_birr(self, item):
        return item.get_fob_value_birr()

    def dehydrate_unit_price_birr(self, item):
        return item.get_unit_price_birr()

    def dehydrate_allocated_cost(self, item):
        return item.allocated_cost

    def dehydrate_total_cost(self, item):
        return item.total_cost

    def dehydrate_unit_landed_cost(self, item):
        return item.unit_landed_cost

    def dehydrate_suggested_price(self, item):
        return item.get_suggested_selling_price()

    def dehydrate_quantity_remaining(self, item):
        return item.quantity_remaining

    class Meta:
        model = ShipmentItem
        fields = (
            'shipment_ref', 'product_name', 'batch_number', 'expiry_date', 'quantity',
            'unit_price',
            'fob_usd', 'fob_birr', 'unit_price_birr',
            'cost_share_percent', 'allocated_cost',
            'total_cost', 'unit_landed_cost', 'suggested_price',
            'quantity_remaining'
        )


# ---------------------- Shipment Resource ----------------------
class ShipmentResource(resources.ModelResource):
    total_fob_usd = fields.Field(column_name='Total FOB USD')
    total_fob_birr = fields.Field(column_name='Total FOB ETB')
    cif_birr = fields.Field(column_name='CIF ETB')

    def dehydrate_total_fob_usd(self, shipment):
        return shipment.get_total_fob()

    def dehydrate_total_fob_birr(self, shipment):
        return shipment.get_total_fob_birr()

    def dehydrate_cif_birr(self, shipment):
        return shipment.get_cif_birr()

    def dehydrate_total_additional_cost(self, shipment):
        return shipment.total_additional_cost

    class Meta:
        model = Shipment
        fields = (
            'reference',
            'exchange_rate',
            'total_fob_usd',
            'total_fob_birr',
            'cif_birr',
            'custom_duty_percent',
            'custom_duty_amount',
            'total_additional_cost',
            'created_at'
        )


# ---------------------- Inline ----------------------
class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 1

    readonly_fields = (
        'fob_value',
        'get_fob_birr',
        'cost_share_percent',
        'allocated_cost',
        'total_cost',
        'unit_landed_cost',
        'get_selling_price',
        'quantity_remaining',
    )

    def get_fob_birr(self, obj):
        return obj.get_fob_value_birr()
    get_fob_birr.short_description = "FOB (ETB)"

    def get_selling_price(self, obj):
        return obj.get_suggested_selling_price()
    get_selling_price.short_description = "Selling Price (ETB)"


# ---------------------- Shipment Admin ----------------------
class ShipmentAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ShipmentResource

    list_display = (
        'reference',
        'exchange_rate',
        'total_fob',
        'get_total_fob_birr',
        'get_cif_birr',
        'custom_duty_percent',
        'custom_duty_amount',
        'total_additional_cost',
        'created_at',
    )

    inlines = [ShipmentItemInline]

    readonly_fields = (
        'total_fob',
        'get_total_fob_birr',
        'get_cif_birr',
        'custom_duty_amount',
        'total_additional_cost',
    )

    fieldsets = (
        ("Basic Info", {
            'fields': ('reference', 'exchange_rate')
        }),
        ("Cost Inputs", {
            'fields': (
                'insurance',
                'freight_documentation',
                'bank_lc_charge',
                'inland_transport',
                'storage_modjo',
                'demurrage',
                'loading_unloading',
                'scanning',
                'rent',
                'professional_salary',
            )
        }),
        ("Tax Settings", {
            'fields': ('custom_duty_percent',)
        }),
        ("Calculated", {
            'fields': (
                'total_fob',
                'get_total_fob_birr',
                'get_cif_birr',
                'custom_duty_amount',
                'total_additional_cost'
            ),
        }),
    )

    def total_fob(self, obj):
        return obj.get_total_fob()
    total_fob.short_description = "FOB (USD)"

    def get_total_fob_birr(self, obj):
        return obj.get_total_fob_birr()
    get_total_fob_birr.short_description = "FOB (ETB)"

    def get_cif_birr(self, obj):
        return obj.get_cif_birr()
    get_cif_birr.short_description = "CIF (ETB)"


# ---------------------- ShipmentItem Admin ----------------------
class ShipmentItemAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ShipmentItemResource

    list_display = (
        'shipment',
        'product',
        'batch_number',
        'expiry_date',
        'quantity',
        'unit_price',
        'get_fob_usd',
        'get_fob_birr',
        'cost_share_percent',
        'allocated_cost',
        'total_cost',
        'unit_landed_cost',
        'get_selling_price',
        'quantity_remaining',
    )

    readonly_fields = (
        'fob_value',
        'cost_share_percent',
        'allocated_cost',
        'total_cost',
        'unit_landed_cost',
        'quantity_remaining',
    )

    def get_fob_usd(self, obj):
        return obj.get_fob_value()
    get_fob_usd.short_description = "FOB (USD)"

    def get_fob_birr(self, obj):
        return obj.get_fob_value_birr()
    get_fob_birr.short_description = "FOB (ETB)"

    def get_selling_price(self, obj):
        return obj.get_suggested_selling_price()
    get_selling_price.short_description = "Selling Price (ETB)"


# ✅ FINAL REGISTRATION
custom_admin_site.register(Shipment, ShipmentAdmin)
custom_admin_site.register(ShipmentItem, ShipmentItemAdmin)
