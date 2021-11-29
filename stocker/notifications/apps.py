from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stocker.notifications'

    CRON_INTERVAL_SEC = 60

    def ready(self):
        from . import signals
