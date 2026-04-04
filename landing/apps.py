from django.apps import AppConfig


class LandingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "landing"   # ✅ MUST match folder name

    def ready(self):
        try:
            import landing.signals  # ✅ corrected import
        except ImportError:
            pass  # avoids crash if signals.py does not exist
