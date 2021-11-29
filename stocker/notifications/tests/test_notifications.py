import logging
import pytest
from datetime import (
    datetime as DateTime,
    time as Time,
    timedelta as TimeDelta,
    timezone as TimeZone,
)
from unittest import mock
from .. import tasks
from ..services import TickerStateDto
from ..models import (
    Tick,
    Exchange,
    Ticker,
    Notification,
)

_logger = logging.getLogger(__name__)


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send')
def test_price_went_up_by_step_send_notification(
        mock_send,
        step_notification,
        tick
):
    # arrange
    price_notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )
    price_tick = tick(value=3.5, property=Ticker.Properties.PRICE)

    # act (price rose by 0.5)
    tick(value=4.0, property=Ticker.Properties.PRICE)

    # assert
    mock_send.assert_called_once()


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send')
def test_price_went_down_by_step_send_notification(
        mock_send,
        step_notification,
        tick
):
    # arrange
    price_notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )
    price_tick = tick(value=3.5, property=Ticker.Properties.PRICE)

    # act (price went down by 0.5)
    tick(value=3.0, property=Ticker.Properties.PRICE)

    # assert (notification has been sent)
    mock_send.assert_called_once()


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send')
def test_price_changed_but_change_is_too_small_to_send(
        mock_send,
        step_notification,
        tick
):
    # arrange
    price_notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )
    price_tick = tick(value=3.5, property=Ticker.Properties.PRICE)

    # act
    tick(value=3.99, property=Ticker.Properties.PRICE)

    # assert
    mock_send.assert_not_called()


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send')
def test_price_fluctuate_send_no_notification(
        mock_send,
        step_notification,
        tick
):
    # arrange
    notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )
    fluctuations = 5
    fluct_value = 0.1
    open_price = 3.5
    price_tick = tick(value=open_price, property=Ticker.Properties.PRICE)

    # act
    for i in range(1, fluctuations):
        tick(value=open_price + i*fluct_value, property=Ticker.Properties.PRICE)

    for i in range(1, fluctuations):
        tick(value=open_price - i*fluct_value, property=Ticker.Properties.PRICE)

    # assert
    mock_send.assert_not_called()


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send')
def test_price_changes_triggers_multiple_notifications(
        mock_send,
        step_notification,
        tick
):
    # arrange
    notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )
    price_tick = tick(value=3.5, property=Ticker.Properties.PRICE)

    # act
    tick(value=4.0, property=Ticker.Properties.PRICE)
    tick(value=4.2, property=Ticker.Properties.PRICE)
    tick(value=4.5, property=Ticker.Properties.PRICE)
    tick(value=6.0, property=Ticker.Properties.PRICE)
    tick(value=5.7, property=Ticker.Properties.PRICE)
    tick(value=5.5, property=Ticker.Properties.PRICE)

    # assert
    assert mock_send.call_count == 4


@pytest.mark.django_db
@mock.patch('stocker.notifications.tasks.send_email')
def test_tasks_send_notification_send_email(
        mock_send_email,
        step_notification,
        tick
):
    # arrange
    email_notification = step_notification(
        change=0.5,
        property=Ticker.Properties.PRICE,
        type=Notification.Types.EMAIL,
    )

    tasks.send(email_notification)

    # assert
    mock_send_email.delay.assert_called_once()

@pytest.mark.django_db
def test_interval_notification():
    notification =


@pytest.mark.django_db
@mock.patch('stocker.notifications.models.Exchange.is_open')
@mock.patch('stocker.notifications.services.YahooTickerProvider.current_state')
def test_save_requested_ticker_dto_state(mock_current_state, mock_is_open, tick, step_notification):
    # arrange
    expected_ticks = 5
    mock_is_open.return_value = True
    # mock call to the external api
    mock_current_state.return_value = TickerStateDto(
        price=3.85,
        ask=3.86,
        bid=3.84,
        ask_size=300,
        bid_size=400,
        currency='USD'
    )
    step_notification(
        type=Notification.Types.EMAIL,
        property=Ticker.Properties.PRICE,
        change=0.5
    )

    # act
    tasks.request_yahoo_api()

    # assert
    mock_current_state.assert_called_once()
    assert Tick.objects.count() == expected_ticks


@pytest.mark.parametrize(
    ['opens_at', 'closes_at', 'current_time', 'is_open'],
    [
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=14, minute=30), True),
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=18, minute=30), True),
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=21, minute=30), True),
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=14, minute=29), False),
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=21, minute=31), False),
        (Time(hour=14, minute=30), Time(hour=21, minute=30), Time(hour=0, minute=0), False),
    ]
)
@pytest.mark.django_db
@mock.patch('stocker.notifications.models.datetime')
def test_exchange_is_open_at_time(mock_datetime, opens_at, closes_at, current_time, is_open):
    # any work day
    test_time = DateTime(year=2021, month=11, day=1, hour=15, minute=30,
                         tzinfo=TimeZone.utc)
    mock_datetime.utcnow.return_value = test_time.replace(
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
    assert exchange.is_open() == is_open


@pytest.mark.django_db
@mock.patch('stocker.notifications.models.datetime')
def test_exchange_is_open_on_weekday(datetime_mock, nasdaq):
    def exchange_week_iterate(start, stop, assert_open):
        some_monday = DateTime(year=2021, month=11, day=1, hour=15, minute=30,
                               tzinfo=TimeZone.utc)
        for day_number in range(start, stop):
            next_day = some_monday + TimeDelta(days=day_number)
            datetime_mock.utcnow.return_value = next_day
            assert nasdaq.is_open() == assert_open

    # monday friday
    work_week = (0, 5)
    exchange_week_iterate(*work_week, True)

    # saturday, sunday
    weekend = (5, 7)
    exchange_week_iterate(*weekend, False)
