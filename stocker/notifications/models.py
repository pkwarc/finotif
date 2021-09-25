from django.db import models
from django.contrib.auth.models import User

DECIMAL_MAX_DIGITS = 12
DECIMAL_PRECISION = 2


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TimestampedModel(CreatedAtModel):
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DescriptiveTimestampedModel(TimestampedModel):
    name = models.TextField()
    description = models.TextField()

    class Meta:
        abstract = True


class Exchange(DescriptiveTimestampedModel):
    pass


class Ticker(DescriptiveTimestampedModel):
    symbol = models.TextField()
    short_name = models.TextField()
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)


class TickerState(CreatedAtModel):
    price = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS,
                                decimal_places=DECIMAL_PRECISION)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)


class NotificationType(DescriptiveTimestampedModel):
    pass


class Notification(TimestampedModel):
    title = models.TextField()
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class PriceStepNotification(Notification):
    step = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS,
                               decimal_places=DECIMAL_PRECISION)


class PriceStepTickerState(TimestampedModel):
    step = models.ForeignKey(PriceStepNotification, on_delete=models.CASCADE)
    last_step_at = models.ForeignKey(TickerState, on_delete=models.CASCADE)
