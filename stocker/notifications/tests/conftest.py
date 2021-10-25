import pytest
from ..models import (
    User,
    Exchange,
    Ticker,
    TickerState,
    PriceStepNotification,
    Currency,
)


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
    class UserFactory:
        PASSWORD = 'test123!RF'

        def __init__(self):
            self._counter = 0

        def get(self):
            suffix = self._counter
            self._counter += 1
            return User.objects.create_user(
                username=f'test_user_{suffix}',
                email=f'test_user_{suffix}@email.com',
                password=UserFactory.PASSWORD
            )
    return UserFactory()


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
            user=user.get(),
            ticker=ticker,
            title=title,
            content=content,
            step=step
        )

    return _produce
