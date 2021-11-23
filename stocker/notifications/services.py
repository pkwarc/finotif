import logging
from dataclasses import dataclass
from yfinance import utils
from django.contrib.auth.models import AbstractUser
from typing import Optional


_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TickerStateDto:
    currency: str = ''
    price: float = 0
    ask: float = 0
    bid: float = 0
    ask_size: float = 0
    bid_size: float = 0


@dataclass(frozen=True)
class TickerDto:
    symbol: str = ''
    name: str = ''
    short_name: str = ''
    description: str = ''
    exchange: str = ''
    state: TickerStateDto = None


class YahooTickerProvider:

    def __init__(self, symbol: str):
        self._base_url = 'https://query2.finance.yahoo.com'
        self._scrape_url = 'https://finance.yahoo.com/quote'
        self._symbol = symbol.strip().upper()

    def _request_data_ticker(self):
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
        return None

    def info(self) -> Optional[TickerDto]:
        return self._request_data_ticker()

    def current_state(self) -> Optional[TickerStateDto]:
        data = self._request_data_ticker()
        if data:
            return data.state
        else:
            return None

    def __repr__(self):
        return f'services.{self.__class__.__name__}({self._symbol})'

