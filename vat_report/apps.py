from django.apps import AppConfig

class VatReportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vat_report'

    def ready(self):
        import vat_report.signals
