from django.core import mail
from celery import shared_task
from celery.utils.log import get_task_logger
from .services import YahooTickerProvider
from .apps import NotificationsConfig as conf

_logger = get_task_logger(__name__)


@shared_task
def send_email(to: str, subject: str, content: str):
    _logger.info('Sending email to {0}'.format(to))
    mail.send_mail(
        subject,
        content,
        conf.EMAIL_FROM
        [to],
        fail_silently=False
    )


@shared_task
def send_push(to):
    _logger.info('Sending push to {0}'.format(to))


@shared_task
def request_yahoo_api():
    from .models import (
        Currency,
        Ticker,
        TickerState,
    )

    tickers = (Ticker.objects
               .select_related('exchange')
               .filter(pricestepnotification__is_active=True)
               .distinct())
    currencies = Currency.objects.all()
    symbol_currency = {currency.symbol: currency for currency in currencies}
    for ticker in tickers:
        if not ticker.exchange.is_open():
            continue
        symbol = ticker.symbol
        provider = YahooTickerProvider(symbol)
        state = provider.current_state()
        current_state = TickerState(
            ticker=ticker,
            price=state.price,
            ask=state.ask,
            bid=state.bid,
            ask_size=state.ask_size,
            bid_size=state.bid_size,
            currency=symbol_currency[state.currency]
        )
        current_state.save()
