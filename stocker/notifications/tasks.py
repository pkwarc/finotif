from celery import shared_task
from celery.utils.log import get_task_logger
import requests

logger = get_task_logger(__name__)

YAHOO_URL = 'http://www.yahoo.com'


@shared_task
def send_email(to, subject, content):
    logger.warning('Sending email to {0}'.format(to))


@shared_task
def send_push(to):
    logger.info('Sending push to {0}'.format(to))


@shared_task
def query_yahoo_api():
    logger.info('Requesting {0}...'.format(YAHOO_URL))
    #ticker = yfinance.Ticker('TELL')
    #logger.info(ticker.info)
    response = requests.get(YAHOO_URL)
    return response
