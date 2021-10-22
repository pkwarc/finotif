import logging
import pytest
from datetime import datetime, time
from unittest import mock
from ..tasks import request_yahoo_api
from ..services import TickerStateDto
from ..models import (
    Exchange,
    TickerState,
    Notification,
    PriceStepNotificationState,
)

_logger = logging.getLogger(__name__)


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


@pytest.mark.parametrize(
    ['opens_at', 'closes_at', 'current_time', 'is_open'],
    [
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=14, minute=30), True),
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=18, minute=30), True),
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=21, minute=30), True),
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=14, minute=29), False),
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=21, minute=31), False),
        (time(hour=14, minute=30), time(hour=21, minute=30), time(hour=0, minute=0), False),
    ]
)
@pytest.mark.django_db
@mock.patch('stocker.notifications.models.datetime')
def test_exchange_is_open(datetime_mock, opens_at, closes_at, current_time, is_open):
    test_time = datetime.utcnow()
    datetime_mock.utcnow.return_value = test_time.replace(
        hour=current_time.hour,
        minute=current_time.minute,
        second=current_time.second,
        microsecond=0
    )
    exchange = Exchange(
        name='TEST',
        mic='TST',
        opens_at=opens_at,
        closes_at=closes_at
    )
    exchange.save()
    is_open_result = exchange.is_open()
    assert exchange.is_open() == is_open
