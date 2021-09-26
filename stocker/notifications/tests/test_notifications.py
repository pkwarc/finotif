import logging
import pytest
from django.contrib.auth.models import User
from ..models import (
    Exchange,
    Ticker,
    TickerState,
    Notification,
    PriceStepNotification,
    PriceStepNotificationState,
    Currency,
)

_logger = logging.getLogger(__name__)


@pytest.fixture
def exchange():
    exchange = Exchange(name='test', description='test exchange')
    exchange.save()
    return exchange


@pytest.fixture
def ticker(exchange):
    tell = Ticker(symbol='TELL',
                  short_name='Tellurian',
                  name='Tellurian Inc.',
                  exchange=exchange)
    tell.save()
    return tell


@pytest.fixture
def user():
    return User.objects.create_user(username='Testname',
                                    email='testemail@test.com',
                                    password='test123!RF')


@pytest.fixture
def usd():
    usd = Currency(symbol='USD')
    usd.save()
    return usd


@pytest.mark.django_db
def test_new_notification_set_starting_point(ticker, usd, user):
    base_ticker_state = TickerState.objects.create(
        price=3.45,
        ask=3.47,
        bid=3.44,
        ask_size=4000,
        bid_size=3000,
        currency=usd,
        ticker=ticker
    )
    step_notification = PriceStepNotification.create(
        starting_point=base_ticker_state,
        type=Notification.Types.EMAIL,
        user=user,
        ticker=ticker,
        title='TELL price changed',
        content='Some content',
        step=0.5
    )
    assert (PriceStepNotificationState.objects
            .filter(notification=step_notification,
                    last_step=base_ticker_state)
            .get())


@pytest.mark.django_db
def test_price_changed_send_notification(ticker, user):
    # send an email when price changes by 0.5

    assert True
