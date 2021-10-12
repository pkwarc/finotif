import logging
import pytest
import datetime
from unittest import mock
from django.contrib.auth.models import User
from ..tasks import request_yahoo_api
from ..services import TickerStateDto
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
def nasdaq():
    return Exchange.objects.filter(mic='XNAS').get()


@pytest.fixture
def default_ticker(nasdaq):
    return Ticker.objects.create(
        symbol='TELL',
        short_name='Tellurian',
        name='Tellurian Inc.',
        exchange=nasdaq
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        username='Testname',
        email='testemail@test.com',
        password='test123!RF'
    )


@pytest.fixture
def usd():
    return Currency.objects.filter(symbol='USD').get()


@pytest.fixture
def ticker_state(usd, default_ticker):
    def _produce(price=10.0, ask=11.0, bid=9.0, ask_size=3000,
                 bid_size=4000, currency=usd, ticker=default_ticker):
        return TickerState.objects.create(
            price=price,
            ask=ask,
            bid=bid,
            ask_size=ask_size,
            bid_size=bid_size,
            currency=currency,
            ticker=ticker
        )

    return _produce


@pytest.fixture
def price_notification(default_ticker, user):
    default_title = default_ticker.name + ' price changed',
    default_content = 'Some content about' + default_ticker.name

    def _produce(starting_point, type, step, ticker=default_ticker,
                 title=default_title, content=default_content):
        return PriceStepNotification.create(
            starting_point=starting_point,
            type=type,
            user=user,
            ticker=ticker,
            title=title,
            content=content,
            step=step
        )

    return _produce


@pytest.mark.django_db
def test_new_notification_set_starting_point(price_notification, ticker_state):
    base_ticker_state = ticker_state(price=3.45)
    step_notification = price_notification(
        starting_point=base_ticker_state,
        type=Notification.Types.EMAIL,
        step=0.5
    )

    assert (PriceStepNotificationState.objects
            .filter(notification=step_notification,
                    last_step=base_ticker_state)
            .get())


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send_email')
def test_price_changed_send_email_notification(mock_send_email, price_notification, ticker_state):
    # arrange
    base_ticker_state = ticker_state(price=3.5)
    step_notification = price_notification(
        starting_point=base_ticker_state,
        type=Notification.Types.EMAIL,
        step=0.5
    )

    # act
    ticker_state(price=4.0)

    # assert
    mock_send_email.delay.assert_called_once()


@pytest.mark.django_db
@mock.patch('stocker.notifications.models.Notification.send')
def test_price_changed_but_change_is_too_small_to_send(mock_send,
                                                       price_notification,
                                                       ticker_state):
    # arrange
    base_ticker_state = ticker_state(price=3.5)
    step_notification = price_notification(
        starting_point=base_ticker_state,
        type=Notification.Types.EMAIL,
        step=0.5
    )

    # act
    ticker_state(price=3.99)

    # assert
    mock_send.assert_not_called()


@pytest.mark.django_db
@mock.patch('stocker.notifications.models.Notification.send')
def test_multiple_price_changes_when_change_eq_step(mock_send,
                                                    price_notification,
                                                    ticker_state):
    # arrange
    number_of_changes = 10
    step = 0.1
    open_price = 3.5
    base_ticker_state = ticker_state(price=open_price)
    step_notification = price_notification(
        starting_point=base_ticker_state,
        type=Notification.Types.EMAIL,
        step=step
    )

    # act
    price = open_price
    for i in range(number_of_changes):
        price = price + step
        ticker_state(price=price)

    # assert
    assert mock_send.call_count == number_of_changes


@pytest.mark.django_db
@mock.patch('stocker.notifications.services.YahooTickerProvider.current_state')
def test_save_requested_ticker_dto_state(mock_current_state, ticker_state, price_notification):
    # arrange
    expected_states = 2
    mock_current_state.return_value = TickerStateDto(
        price=3.85,
        ask=3.86,
        bid=3.84,
        ask_size=300,
        bid_size=400,
        currency='USD'
    )
    price_notification(
        starting_point=ticker_state(price=3),
        type=Notification.Types.EMAIL,
        step=0.5
    )

    # act
    request_yahoo_api()

    # assert
    mock_current_state.assert_called_once()
    assert TickerState.objects.count() == expected_states
