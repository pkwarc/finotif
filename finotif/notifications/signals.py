from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    Tick,
    StepNotification,
)
from . import tasks


@receiver(post_save, sender=Tick)
def ticker_value_changed(sender, instance, **kwargs):
    notifications = StepNotification.objects.filter(
        ticker=instance.ticker
    ).filter(
        is_active=True
    )
    for notification in notifications:
        if notification.should_send(instance):
            tasks.send(notification)
