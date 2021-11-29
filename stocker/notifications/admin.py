import logging
from django.contrib import admin
from django.apps import apps

_logger = logging.getLogger(__name__)

# Register your models here.
app = apps.get_app_config('notifications')

for _, model in app.models.items():
    admin.site.register(model)

