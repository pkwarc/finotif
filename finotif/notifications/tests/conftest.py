import pytest
from ..models import (
    User,
    Exchange,
    Ticker,
    Tick,
    StepNotification,
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
def tick(usd, default_ticker):
    def _produce(
            value,
            property,
            currency=usd,
            ticker=default_ticker
    ):
        return Tick.objects.create(
            value=value,
            property=property,
            currency=currency,
            ticker=ticker
        )

    return _produce


@pytest.fixture
def step_notification(default_ticker, user):
    default_title = default_ticker.name + ' price changed',
    default_content = 'Some content about' + default_ticker.name

    def _produce(
            property,
            type,
            change,
            is_active=True,
            ticker=default_ticker,
            title=default_title,
            content=default_content
    ):
        return StepNotification.objects.create(
            property=property,
            type=type,
            change=change,
            user=user.get(),
            ticker=ticker,
            title=title,
            content=content,
        )

    return _produce
