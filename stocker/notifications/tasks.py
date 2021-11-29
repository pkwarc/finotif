from datetime import datetime as DateTime
from django.core import mail
from celery import shared_task
from celery.utils.log import get_task_logger
from .services import YahooTickerProvider
from .models import (
    Notification,
    IntervalNotification,
    Ticker,
    Tick,
)

_logger = get_task_logger(__name__)


def send(notification):
    type = notification.type
    if type == Notification.Types.EMAIL:
        send_email.delay(
            notification.user.email,
            notification.title,
            notification.content
        )
    elif type == Notification.Types.PUSH:
        send_push.delay(notification)
    else:
        _logger.warning(f'Cannot send notification - unknown type {type}')


@shared_task
def send_email(to: str, subject: str, content: str):
    result = mail.send_mail(
        subject=subject,
        message=content,
        from_email=None,
        recipient_list=[to],
        fail_silently=False
    )
    _logger.info(f'Sending email to = {to}, result={result}')


@shared_task
def send_push(notification):
    # TODO:
    _logger.warning(f'No push sent')


@shared_task
def send_interval_notifications():
    notifications = IntervalNotification.select_related(
        'last_tick'
    ).select_related(
        'ticker__exchange'
    ).filter(
        is_active=True
    )
    now = DateTime.utcnow()
    for notification in notifications:
        if not notification.ticker.exchange.is_open():
            continue
        interval = notification.interval
        last_time = notification.last_tick.created_at
        if last_time + interval >= now:
            send(notification)
            last_tick = Tick.objects.filter(
                ticker=notification.ticker
            ).order_by('-pk').last()
            if last_tick:
                notification.last_tick = last_tick
                notification.save()
            else:
                _logger.warning(
                    f'Failed to find last_tick for '
                    f'the IntervalNotification {notification}'
                )


@shared_task
def request_yahoo_api():
    tickers = (Ticker.objects
               .select_related('exchange')
               .filter(stepnotification__is_active=True)
               .distinct())
    for ticker in tickers:
        if not ticker.exchange.is_open():
            continue
        symbol = ticker.symbol
        provider = YahooTickerProvider(symbol)
        state = provider.current_state()
        Tick.save_ticks(state, ticker)
