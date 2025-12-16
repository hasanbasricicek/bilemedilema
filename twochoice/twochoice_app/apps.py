from django.apps import AppConfig


class TwochoiceAppConfig(AppConfig):
    name = 'twochoice_app'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import twochoice_app.signals
