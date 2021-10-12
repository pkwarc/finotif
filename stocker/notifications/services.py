import logging
from dataclasses import dataclass
from yfinance import utils
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError,
)

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TickerStateDto:
    currency: str = ''
    price: float = 0
    ask: float = 0
    bid: float = 0
    ask_size: float = 0
    bid_size: float = 0

    def is_valid(self) -> bool:
        return (self.price > 0
                and self.ask > 0
                and self.bid > 0
                and self.ask_size > 0
                and self.bid_size > 0
                and self.currency)


@dataclass(frozen=True)
class TickerDto:
    symbol: str = ''
    name: str = ''
    short_name: str = ''
    description: str = ''
    exchange: str = ''
    state: TickerStateDto = TickerStateDto()

    def is_valid(self) -> bool:
        return (self.symbol
                and self.name
                and self.short_name
                and self.exchange
                and self.state.is_valid())


class YahooTickerProvider:

    def __init__(self, symbol: str):
        self._base_url = 'https://query2.finance.yahoo.com'
        self._scrape_url = 'https://finance.yahoo.com/quote'
        self._symbol = symbol.upper()
        self._cached = None

    def _request_data_ticker(self) -> TickerDto:
        ticker_url = f'{self._scrape_url}/{self._symbol}'
        _logger.info('Requesting {0}...'.format(ticker_url))
        data = utils.get_json(ticker_url)
        if data:
            try:
                state = TickerStateDto(
                    price=data['financialData']['currentPrice'],
                    ask=data['summaryDetail']['ask'],
                    bid=data['summaryDetail']['bid'],
                    ask_size=data['summaryDetail']['askSize'],
                    bid_size=data['summaryDetail']['bidSize'],
                    currency=data['summaryDetail']['currency'].upper(),
                )
                ticker = TickerDto(
                    symbol=data['symbol'],
                    name=data['quoteType']['longName'],
                    short_name=data['quoteType']['shortName'],
                    description=data['summaryProfile']['longBusinessSummary'],
                    exchange=data['price']['exchangeName'].upper(),
                    state=state
                )
                self._cached = ticker
                return ticker
            except KeyError:
                msg = f'Error during parsing {self!r}'
                _logger.error(msg + f' {data!r}')
        return TickerDto()

    def info(self) -> TickerDto:
        if self._cached:
            return self._cached
        else:
            self._cached = self._request_data_ticker()
            return self._cached

    def current_state(self, refresh=True) -> TickerStateDto:
        if refresh:
            return self._request_data_ticker().state
        else:
            return self.info().state

    def __repr__(self):
        return f'services.{self.__class__.__name__}({self._symbol})'


def get_or_create_ticker(symbol: str, exchange_mic: str, provider=None):
    from .models import (
        Ticker,
        Exchange
    )
    if not provider:
        provider = YahooTickerProvider(symbol=symbol)
    try:
        exchange = Exchange.objects.filter(mic=exchange_mic).get()
    except Exchange.DoesNotExist:
        raise ValidationError(('Market Identifier Code (MIC) '
                               f'"{exchange_mic}" is not supported'))
    ticker = Ticker.objects.filter(
        symbol=symbol.upper().strip()
    ).first()
    if ticker is None:
        ticker_info = provider.info()
        if ticker_info.is_valid():
            ticker = Ticker(
                symbol=ticker_info.symbol.upper().strip(),
                short_name=ticker_info.short_name,
                name=ticker_info.name,
                description=ticker_info.description,
                exchange=exchange
            )
            ticker.save()
        else:
            raise APIException(
                status.HTTP_404_NOT_FOUND,
                f'Ticker {symbol} does not exist'
            )
    return ticker


def save_ticker_state(ticker, state: TickerStateDto):
    from .models import TickerState, Currency
    currencies = Currency.objects.all()
    symbol_currency = {currency.symbol: currency for currency in currencies}
    current_state = TickerState.objects.create(
        ticker=ticker,
        price=state.price,
        ask=state.ask,
        bid=state.bid,
        ask_size=state.ask_size,
        bid_size=state.bid_size,
        currency=symbol_currency[state.currency]
    )
    return current_state


def create_price_step_notification(data: dict, provider=None):
    from .models import PriceStepNotification
    symbol = data['symbol']
    exchange_mic = data['exchange']
    if not provider:
        provider = YahooTickerProvider(symbol=symbol)
    ticker = get_or_create_ticker(symbol, exchange_mic, provider)
    last_state = save_ticker_state(ticker, provider.current_state())
    try:
        user = User.objects.get(pk=1)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='Testname',
            email='testemail@test.com',
            password='test123!RF'
        )
    notification = PriceStepNotification.create(
        starting_point=last_state,
        title=data['title'],
        content=data['content'],
        type=data['type'],
        is_active=data['is_active'],
        step=data['step'],
        ticker=ticker,
        user=user
    )
    return notification
