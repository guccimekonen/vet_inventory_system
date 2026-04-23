from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from import_export.admin import ExportMixin
from import_export import resources, fields

from .models import Sale
from dashboard.admin import custom_admin_site


APPROVER_GROUP_NAMES = {"Admin", "Manager", "Sales Manager"}


class SaleAdminForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request is not None:
            can_approve = (
                self.request.user.is_superuser
                or self.request.user.groups.filter(name__in=APPROVER_GROUP_NAMES).exists()
            )

            if not can_approve and "status" in self.fields:
                self.fields.pop("status")

    def clean(self):
        cleaned_data = super().clean()

        if "status" not in cleaned_data or not cleaned_data.get("status"):
            cleaned_data["status"] = Sale.STATUS_PENDING

        if "stock_applied" not in cleaned_data or cleaned_data.get("stock_applied") is None:
            cleaned_data["stock_applied"] = False

        return cleaned_data


class SaleResource(resources.ModelResource):
    product_name = fields.Field(column_name="Product Name")
    status_value = fields.Field(column_name="Status")
    requested_by_value = fields.Field(column_name="Requested By")
    approved_by_value = fields.Field(column_name="Approved By")
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

    def dehydrate_status_value(self, sale):
        return sale.status

    def dehydrate_requested_by_value(self, sale):
        return sale.requested_by.username if sale.requested_by else ""

    def dehydrate_approved_by_value(self, sale):
        return sale.approved_by.username if sale.approved_by else ""

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
            "status_value",
            "requested_by_value",
            "approved_by_value",
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
            "approved_at",
        )


class SaleAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SaleResource
    form = SaleAdminForm

    list_display = (
        "compact_product",
        "status",
        "requested_by",
        "approved_by",
        "get_batch_number",
        "quantity",
        "unit_price",
        "get_total",
        "get_wht_amount",
        "get_net_payable",
        "sale_date",
        "approved_at",
    )

    search_fields = (
        "product__name",
        "product__sku",
        "customer_name",
        "requested_by__username",
        "approved_by__username",
    )
    list_filter = ("status", "sale_date", "product", "requested_by", "approved_by")
    actions = ("approve_selected_sales", "reject_selected_sales")

    @admin.display(description="Product", ordering="product__sku")
    def compact_product(self, obj):
        if not obj.product:
            return "-"

        return format_html(
            '<div class="compact-product-cell"><strong>{}</strong><br><span>{}</span></div>',
            obj.product.sku or "-",
            obj.product.name or "-",
        )

    readonly_fields = (
        "requested_by",
        "approved_by",
        "approved_at",
        "stock_applied",
        "consumed_batch_number",
        "consumed_expiry_date",
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

    fieldsets = (
        ("Sale Request", {
            "fields": (
                "product",
                "quantity",
                "unit_price",
                "discount_percent",
                "vat_percent",
                "wht_percent",
                "status",
                "rejection_reason",
            )
        }),
        ("Customer Information", {
            "fields": (
                "customer_name",
                "customer_phone",
                "customer_email",
                "customer_vat",
                "customer_city",
                "customer_address",
            )
        }),
        ("Workflow", {
            "fields": (
                "requested_by",
                "approved_by",
                "approved_at",
                "stock_applied",
                "consumed_batch_number",
                "consumed_expiry_date",
            )
        }),
        ("Calculated Values", {
            "fields": (
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
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        base_form = super().get_form(request, obj, **kwargs)

        class RequestAwareSaleAdminForm(base_form):
            def __new__(cls, *args, **inner_kwargs):
                inner_kwargs["request"] = request
                return base_form(*args, **inner_kwargs)

        return RequestAwareSaleAdminForm

    def user_can_approve(self, user):
        return user.is_superuser or user.groups.filter(name__in=APPROVER_GROUP_NAMES).exists()

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("product", "requested_by", "approved_by")
        if self.user_can_approve(request.user):
            return qs
        return qs.filter(requested_by=request.user)

    def has_view_permission(self, request, obj=None):
        allowed = super().has_view_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self.user_can_approve(request.user) or obj.requested_by_id == request.user.id

    def has_change_permission(self, request, obj=None):
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed

        if self.user_can_approve(request.user):
            return True

        return obj.requested_by_id == request.user.id and obj.status == Sale.STATUS_PENDING

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))

        if not self.user_can_approve(request.user):
            readonly.extend(["status", "rejection_reason"])

        if obj and obj.status == Sale.STATUS_APPROVED and not request.user.is_superuser:
            readonly.extend([field.name for field in Sale._meta.fields])

        return tuple(dict.fromkeys(readonly))

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])

        if not self.user_can_approve(request.user):
            exclude.append("status")

        return tuple(dict.fromkeys(exclude))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not self.user_can_approve(request.user):
            actions.pop("approve_selected_sales", None)
            actions.pop("reject_selected_sales", None)
        return actions

    @admin.action(description="Approve selected sales")
    def approve_selected_sales(self, request, queryset):
        approved_count = 0

        for sale in queryset:
            if sale.status == Sale.STATUS_APPROVED:
                continue

            try:
                sale.approve(request.user)
                approved_count += 1
            except ValidationError as e:
                self.message_user(request, f"Sale #{sale.id}: {e}", level=messages.ERROR)

        if approved_count:
            self.message_user(
                request,
                f"{approved_count} sale(s) approved successfully.",
                level=messages.SUCCESS,
            )

    @admin.action(description="Reject selected sales")
    def reject_selected_sales(self, request, queryset):
        rejected_count = 0

        for sale in queryset:
            if sale.status == Sale.STATUS_APPROVED:
                self.message_user(
                    request,
                    f"Sale #{sale.id} is already approved and cannot be rejected directly.",
                    level=messages.ERROR,
                )
                continue

            try:
                sale.reject(request.user)
                rejected_count += 1
            except ValidationError as e:
                self.message_user(request, f"Sale #{sale.id}: {e}", level=messages.ERROR)

        if rejected_count:
            self.message_user(
                request,
                f"{rejected_count} sale(s) rejected successfully.",
                level=messages.SUCCESS,
            )

    def save_model(self, request, obj, form, change):
        previous = Sale.objects.get(pk=obj.pk) if change else None
        requested_status = obj.status
        approver = self.user_can_approve(request.user)

        obj.status = obj.status or Sale.STATUS_PENDING
        obj.stock_applied = False if obj.stock_applied is None else obj.stock_applied

        if not obj.requested_by_id:
            obj.requested_by = request.user

        try:
            if not change:
                obj.status = Sale.STATUS_PENDING if not approver else (obj.status or Sale.STATUS_PENDING)
                obj.save()
                self.message_user(request, "Sale request saved successfully.", level=messages.SUCCESS)
                return

            if not approver:
                obj.status = previous.status or Sale.STATUS_PENDING
                obj.save()
                self.message_user(request, "Sale request updated.", level=messages.SUCCESS)
                return

            obj.status = previous.status or Sale.STATUS_PENDING
            obj.save()

            if requested_status != previous.status:
                if requested_status == Sale.STATUS_APPROVED:
                    obj.approve(request.user)
                    self.message_user(request, "Sale approved and stock updated.", level=messages.SUCCESS)
                elif requested_status == Sale.STATUS_REJECTED:
                    obj.reject(request.user, obj.rejection_reason)
                    self.message_user(request, "Sale rejected.", level=messages.SUCCESS)
                else:
                    obj.status = Sale.STATUS_PENDING
                    obj.approved_by = None
                    obj.approved_at = None
                    obj.save(update_fields=["status", "approved_by", "approved_at"])
                    self.message_user(request, "Sale moved back to pending.", level=messages.SUCCESS)
            else:
                self.message_user(request, "Sale updated successfully.", level=messages.SUCCESS)

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
