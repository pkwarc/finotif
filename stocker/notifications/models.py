import logging
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

DECIMAL_MAX_DIGITS = 12
DECIMAL_PRECISION = 2

_logger = logging.getLogger(__name__)


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return 'pk={0},created_at={1}'.format(self.pk,
                                              self.created_at)


class TimestampedModel(CreatedAtModel):
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DescriptiveModel(models.Model):
    name = models.TextField()
    description = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return 'pk={0},name={1}'.format(self.pk, self.name)


class TitleContentModel(models.Model):
    title = models.TextField()
    content = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return 'pk={0},title={1}'.format(self.pk,
                                         self.title)


class Exchange(TimestampedModel, DescriptiveModel):
    pass


class Ticker(TimestampedModel, DescriptiveModel):
    symbol = models.TextField()
    short_name = models.TextField()
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)

    def __str__(self):
        return 'pk={0},symbol={1}'.format(self.pk,
                                          self.symbol)


class Note(TimestampedModel, TitleContentModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)

    def __str__(self):
        return 'pk={0},title={1}'.format(self.pk,
                                         self.title)


class Currency(models.Model):
    symbol = models.CharField(max_length=3,
                              primary_key=True)

    def __str__(self):
        return self.symbol


class TickerState(CreatedAtModel):
    price = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS,
                                decimal_places=DECIMAL_PRECISION)
    ask = models.IntegerField()
    ask_size = models.IntegerField()
    bid = models.IntegerField()
    bid_size = models.IntegerField()
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)


@receiver(post_save, sender=TickerState)
def ticker_state_changed(sender: TickerState, **kwargs):
    ticker_id = sender.ticker_id
    _logger.info('State changed for ticker ')
    notifications = PriceStepNotification.objects.filter(ticker_id=ticker_id)
    for notification in notifications:
        last_step = PriceStepNotificationState.objects.filter(
            notification=notification
        ).order_by('-last_step').first()
        should_send = last_step.price + notification.step >= sender.price
        if should_send:
            print('sending notification...')


class Notification(TimestampedModel, TitleContentModel):
    class Types(models.TextChoices):
        EMAIL = 'em', 'Email'
        PUSH = 'ph', 'Push'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=2,
        choices=Types.choices,
        default=Types.EMAIL
    )
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return 'pk={0},title={1},type={2}'.format(self.pk,
                                                  self.title,
                                                  self.type)


class PriceStepNotification(Notification):
    step = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS,
                               decimal_places=DECIMAL_PRECISION,
                               help_text='Send a notification when the change in a ticker price is equal to the step')

    @staticmethod
    def create(starting_point: TickerState = None, *args, **kwargs):
        """
        Static factory method for creating a `PriceStepNotification`

        Sets a starting point needed for calculating the next notification.
        The starting point should be the latest `TickerState` for this ticker.
        The next notification will be send when the ticker current price
        will be equal to base_price_step.last_step.price + step.
        """
        notification = PriceStepNotification(*args, **kwargs)
        notification.save()
        base_price_step = PriceStepNotificationState(notification=notification,
                                                     last_step=starting_point)
        base_price_step.save()
        return notification


class PriceStepNotificationState(TimestampedModel):
    notification = models.ForeignKey(PriceStepNotification, on_delete=models.CASCADE)
    last_step = models.ForeignKey(TickerState, on_delete=models.CASCADE)
