from django.contrib import admin
from import_export.admin import ExportMixin
from .models import VATReport
from dashboard.admin import custom_admin_site

class VATReportAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('year', 'month', 'total_vat_collected', 'total_wht_deducted', 'total_vat_payable')
    ordering = ('-year', '-month')
    list_filter = ('year', 'month')
    search_fields = ('year', 'month')
    list_per_page = 20
    list_editable = ('total_vat_collected', 'total_wht_deducted')
    readonly_fields = ('total_vat_payable',)

    def total_vat_payable(self, obj):
        return obj.total_vat_collected - obj.total_wht_deducted
    total_vat_payable.short_description = "VAT Payable"

custom_admin_site.register(VATReport, VATReportAdmin)
