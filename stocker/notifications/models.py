import logging
import dataclasses
from datetime import datetime
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from .services import  (
    YahooTickerProvider as TickerProvider,
    TickerStateDto
)
from . import tasks

DECIMAL_MAX_DIGITS = 12
DECIMAL_PRECISION = 2

_logger = logging.getLogger(__name__)


class User(AbstractUser):
    email = models.CharField(
        _('email address'),
        max_length=150,
        unique=True,
        help_text=_('Required.'),
        validators=[validate_email],
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )

    class Meta:
        ordering = 'email',


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
        ordering = 'name',

    def __str__(self):
        return 'pk={0},name={1}'.format(self.pk, self.name)


class TitleContentModel(models.Model):
    title = models.TextField()
    content = models.TextField()

    class Meta:
        abstract = True
        ordering = 'title',

    def __str__(self):
        return 'pk={0},title={1}'.format(self.pk,
                                         self.title)


class Exchange(TimestampedModel, DescriptiveModel):
    """Market hours in the UTC"""

    opens_at = models.TimeField()
    closes_at = models.TimeField()
    mic = models.TextField(
        unique=True,
        help_text='Market Identifier Code'
    )

    class Meta:
        ordering = 'mic',

    def is_open(self):
        now = datetime.utcnow()

        if now.weekday() in (5, 6):
            return False
        time = datetime.utcnow().time()
        return self.opens_at <= time <= self.closes_at


class Ticker(TimestampedModel, DescriptiveModel):
    class Properties(models.IntegerChoices):
        PRICE = 0
        VOLUME = 1
        ASK = 2
        ASK_SIZE = 3
        BID = 4
        BID_SIZE = 5

    symbol = models.TextField(unique=True)
    short_name = models.TextField()
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)

    class Meta:
        ordering = 'symbol',

    @classmethod
    def get_or_create(cls, symbol: str, mic: str):
        symbol = symbol.strip().upper()
        ticker = Ticker.objects.first(symbol=symbol)
        exchange = Exchange.objects.first(mic=mic.strip().upper())
        if exchange is None:
            raise ValidationError(
                f'Market Identifier Code (MIC) "{mic}" is not supported'
            )
        if ticker is None:
            info = TickerProvider(symbol=symbol).info()
            if info:
                ticker = Ticker(
                    symbol=symbol,
                    short_name=info.short_name,
                    name=info.name,
                    description=info.description,
                    exchange=exchange
                )
                ticker.save()
            else:
                raise ValidationError(
                    f'Ticker {symbol} is either invalid or not supported'
                )

        return ticker

    def __str__(self):
        return 'pk={0},symbol={1}'.format(self.pk,
                                          self.symbol)


class Note(TimestampedModel, TitleContentModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Ticker, related_name='notes', on_delete=models.CASCADE)

    def __str__(self):
        return 'pk={0},title={1}'.format(self.pk,
                                         self.title)


class Currency(models.Model):
    symbol = models.CharField(max_length=3,
                              primary_key=True)

    def __str__(self):
        return self.symbol


class Tick(CreatedAtModel):
    """The smallest recognized value by which a property of a security may fluctuate"""

    # ignore fractional rounding errors for now
    value = models.FloatField()

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    property = models.IntegerField(choices=Ticker.Properties.choices)

    @classmethod
    def create_ticks(cls, state: TickerStateDto, ticker: Ticker):
        if not state or not ticker:
            return None
        properties = [prop.lower() for value, prop in Ticker.Properties.choices]
        field_names = [field.name for field in dataclasses.fields(state)
                       if field.type == int and field.name in properties]
        currency = Currency.filter(symbol=state.currency.strip().upper()).first()
        if not currency:
            raise ValidationError(f'Currency ${state.currency} does not exist.')

        ticks = []
        for name in field_names:
            try:
                value = float(getattr(state, name))
                if value > 0:
                    tick = cls.objects.create(
                        value=value,
                        ticker=ticker,
                        currency=state.currency,
                        property=getattr(Ticker.Properties, name.upper())
                    )
                    ticks.append(tick)
            except (ValueError, AttributeError) as er:
                _logger.error(er)
        return ticks


class Notification(TimestampedModel, TitleContentModel):
    class Types(models.TextChoices):
        EMAIL = 'em', 'Email'
        PUSH = 'ph', 'Push'

    type = models.CharField(
        max_length=2,
        choices=Types.choices,
        default=Types.EMAIL
    )
    is_active = models.BooleanField(default=True)
    property = models.IntegerField(choices=Ticker.Properties.choices)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def send(self):
        if self.type == Notification.Types.EMAIL:
            tasks.send_email.delay(self.user.email, self.title, self.content)
        elif self.type == Notification.Types.PUSH:
            tasks.send_push.delay(self.user)
        else:
            _logger.warning(f'Cannot send notification - unknown type ${self.type}')

    @classmethod
    def create_notification(cls, notification_serializer):
        notification_serializer.is_valid(raise_exception=True)
        data = notification_serializer.validated_data
        symbol = data['symbol']
        mic = data['mic']
        ticker = Ticker.get_or_create(symbol, mic)

        return Notification(
            ticker=ticker,
            **data
        ), data

    def __str__(self):
        return 'pk={0},title={1},type={2},is_active={3}'.format(
            self.pk,
            self.title,
            self.type,
            self.is_active
        )


class StepNotification(Notification):
    change = models.FloatField(
        help_text='Send the notification when a property of the ticker '
                  'increased/decreased by the value of this field'
    )
    last_tick = models.ForeignKey(Tick, on_delete=models.CASCADE)

    @classmethod
    def save_notification(cls, notification_serializer):
        notification, data = super().create_notification(notification_serializer)
        change = data['change']
        if change > 0:
            if cls.objects.filter(
                user=notification.user
            ).filter(
                change=change
            ).filter(
                ticker=notification.ticker
            ).first():
                raise ValidationError('Already exists')
            notification.change = change
            notification.save()
            return notification
        else:
            raise ValidationError('"change" should be greater than 0')

    def should_send(self, tick: Tick) -> bool:
        should_send = False
        if self.property == tick.property:
            if self.last_tick is not None:
                should_send = (
                    tick.value >= self.last_tick.value + self.change or
                    tick.value <= self.last_tick.value - self.change
                )

        self.last_tick = tick
        self.save()
        return should_send


class IntervalNotification(Notification):
    interval = models.DurationField(
        help_text='Send a notification every [DD] [[HH:]MM:]ss[.uuuuuu] about the value of a property'
    )
    last_tick = models.ForeignKey(Tick, on_delete=models.CASCADE)

    @classmethod
    def save_notification(cls, notification_serializer):
        notification, data = super().create_notification(notification_serializer)
        interval = data['interval']
        if interval > 0:
            if cls.objects.filter(
                    user=notification.user
            ).filter(
                interval=interval
            ).filter(
                ticker=notification.ticker
            ).first():
                raise ValidationError('Already exists')
            notification.value = data['value']
            notification.save()
            return notification
        else:
            raise ValidationError('"interval" should be greater than 0')


@receiver(post_save, sender=Tick)
def ticker_value_changed(sender, tick, **kwargs):
    notifications = StepNotification.objects.filter(
        ticker=tick.ticker
    ).filter(
        is_active=True
    )
    for notification in notifications:
        if notification.should_send(tick):
            notification.send()
