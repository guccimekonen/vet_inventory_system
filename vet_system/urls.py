from django.contrib import admin
from django.urls import path, include
from dashboard.admin import custom_admin_site  # custom admin site
from dashboard.views import dashboard_view
from vet_system.views import login_view   # 👈 add this

urlpatterns = [
    # Login page
    path('', login_view, name='login'),  # 👈 new login page

    # Custom admin site
    path('admin/', custom_admin_site.urls),

    # Standalone dashboard view
    path('dashboard/', dashboard_view, name='dashboard'),

    # Other apps
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('inventory/', include('inventory.urls')),
    path('purchases/', include('purchases.urls')),
    path('vat/', include('vat_report.urls')),
]
