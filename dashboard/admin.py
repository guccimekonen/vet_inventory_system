from django.contrib import admin
from django.urls import path
from django.contrib.admin import AdminSite
from django.shortcuts import redirect


class CustomAdminSite(AdminSite):
    site_header = "Vet System Admin"
    site_title = "Vet Admin Portal"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        from .views import dashboard_view
        return dashboard_view(request)


custom_admin_site = CustomAdminSite(name="custom_admin")


from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)


from django.db import models


class Dashboard(models.Model):
    class Meta:
        verbose_name = "Dashboard"
        verbose_name_plural = "Dashboard"
        app_label = "dashboard"


@admin.register(Dashboard, site=custom_admin_site)
class DashboardAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect("admin:dashboard")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
