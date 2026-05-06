from django.urls import path, include
from django.views.generic import RedirectView

from dashboard.admin import custom_admin_site
from dashboard.views import dashboard_view

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='home'),
    path('admin/', custom_admin_site.urls),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('inventory/', include('inventory.urls')),
    path('purchases/', include('purchases.urls')),
    path('vat/', include('vat_report.urls')),
]
