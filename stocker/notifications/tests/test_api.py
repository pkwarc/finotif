import json
import logging
import pytest
import urllib.parse
from functools import reduce
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ..models import PriceStepNotification

TEST_SERVER = 'http://testserver'
_logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    client = APIClient()
    yield client


@pytest.mark.django_db
def test_api_workflow(client: APIClient):
    # arrange
    notification_data = {
        'symbol': 'TELL',
        'step': 0.5,
        'title': "TELL's price changed",
        'content': "TELL's price changed",
        'exchange': 'XNAS',
        'type': 'em',
        'is_active': True
    }

    # act
    response = client.post(reverse('pricestepnotification-list'),
                           notification_data, format='json')

    # assert
    data_got = json.loads(response.content)
    notification = PriceStepNotification.objects.first()
    assert notification
    url_want = url_join(TEST_SERVER, reverse("pricestepnotification-list"), str(notification.id))
    assert response.status_code == status.HTTP_201_CREATED \
           and data_got['step'] == notification_data['step'] \
           and data_got['title'] == notification_data['title'] \
           and data_got['type'] == notification_data['type'] \
           and data_got['is_active'] == notification_data['is_active'] \
           and data_got['url'] == url_want


def url_join(*args):
    url = reduce(lambda a, b: urllib.parse.urljoin(a, b), args)
    return url if url.endswith('/') else url + '/'
