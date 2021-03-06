import logging
import dataclasses
from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from .services import (
    YahooTickerProvider as TickerProvider,
    TickerStateDto
)


_logger = logging.getLogger(__name__)


def validate_greater_than_zero(num=0):
    if num <= 0:
        raise ValidationError(f'{num} is not greater than 0.')


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

    symbol = models.TextField(unique=True)
    short_name = models.TextField()
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)

    class Meta:
        ordering = 'symbol',

    @classmethod
    def get_or_create(cls, symbol: str, mic: str):
        symbol = symbol.strip().upper()
        ticker = Ticker.objects.filter(symbol=symbol).first()
        exchange = Exchange.objects.filter(mic=mic.strip().upper()).first()
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


class TickerProperty(models.IntegerChoices):
    PRICE = 0, _('PRICE'),
    VOLUME = 1, _('VOLUME'),
    ASK = 2, _('ASK'),
    ASK_SIZE = 3, _('ASK_SIZE')
    BID = 4, _('BID')
    BID_SIZE = 5, _('BID_SIZE')


class NotificationType(models.IntegerChoices):
    EMAIL = 0, _('EMAIL')
    PUSH = 1, _('PUSH')


class Tick(CreatedAtModel):
    """The smallest recognized value by which a property of a security may fluctuate"""

    # ignore fractional rounding errors for now
    value = models.FloatField()

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    property = models.IntegerField(choices=TickerProperty.choices)

    @classmethod
    def save_ticks(cls, state: TickerStateDto, ticker: Ticker):
        if not state or not ticker:
            return None
        properties = [prop.lower().replace(' ', '_')
                      for value, prop in TickerProperty.choices]
        field_names = [field.name for field in dataclasses.fields(state)
                       if field.type in (int, float) and field.name in properties]
        currency = Currency.objects.filter(symbol=state.currency.strip().upper()).first()
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
                        currency=currency,
                        property=getattr(TickerProperty, name.upper())
                    )
                    ticks.append(tick)
            except (ValueError, AttributeError) as er:
                _logger.error(er)
        return ticks

    def __str__(self):
        return 'pk={0},property={1},value={2},created_at={3}'.format(
            self.pk,
            self.property,
            self.value,
            self.created_at
        )


class Notification(TimestampedModel, TitleContentModel):

    type = models.IntegerField(
        choices=NotificationType.choices,
        default=NotificationType.EMAIL
    )
    is_active = models.BooleanField(default=True)
    property = models.IntegerField(choices=TickerProperty.choices)
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True

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
                  'increased/decreased by the value of this field',
        validators=(validate_greater_than_zero,)
    )
    last_tick = models.ForeignKey(Tick, on_delete=models.CASCADE, null=True)

    @classmethod
    def save_notification(cls, notification_serializer):
        notification_serializer.is_valid(raise_exception=True)
        data = notification_serializer.validated_data
        ticker = Ticker.get_or_create(data.pop('symbol'), data.pop('mic'))
        pk = data.pop('pk')

        exists_query = cls.objects.filter(
            user=data['user']
        ).filter(
            change=data['change']
        ).filter(
            ticker=ticker
        ).exclude(
            pk=pk
        )
        if exists_query.first():
            raise ValidationError('Already exists')
        else:
            defaults = dict(**data, ticker=ticker)
            obj, created = cls.objects.update_or_create(id=pk, defaults=defaults)
            return obj

    def should_send(self, tick: Tick) -> bool:
        should_send = False
        if self.property == tick.property:
            if self.last_tick:
                should_send = (
                    tick.value >= self.last_tick.value + self.change or
                    tick.value <= self.last_tick.value - self.change
                )
            if not self.last_tick or should_send:
                self.last_tick = tick
                self.save()
        return should_send
