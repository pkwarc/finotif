import json
import logging
import pytest
import urllib.parse
from functools import reduce
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ..models import PriceStepNotification, User

TEST_SERVER = 'http://testserver'
_logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    client = APIClient()
    yield client


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        reverse('user-list'),
        reverse('note-list'),
        reverse('ticker-list'),
        reverse('pricestepnotification-list'),
    ],
)
def test_if_not_loggedin_then_unauthorized(client, url):
    assert client.get(url).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_ensure_users_see_only_what_they_own(client, user):
    # Create two users
    password = user.PASSWORD
    user0 = user.get()
    user1 = user.get()
    assert user0.pk != user1.pk
    set_client_jwt(client, user0.username, password)
    user_list0 = json.loads(client.get(reverse('user-list')).content)
    set_client_jwt(client, user1.username, password)
    user_list1 = json.loads(client.get(reverse('user-list')).content)
    assert len(user_list0['results']) == 1
    assert len(user_list1['results']) == 1


@pytest.mark.django_db
def test_api_workflow(client: APIClient):
    # Register a user
    user_data = {
        'username': 'testuser',
        'password': 'test_pass_32!3',
        'email': 'testuser@email.com',
    }
    username = user_data['username']
    password = user_data['password']
    response = client.post(reverse('user-list'), user_data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    user_body = json.loads(response.content)
    assert (
        'password' not in user_body
        and username == user_body['username']
        and user_data['email'] == user_body['email']
    )

    # User login, obtain JWT
    set_client_jwt(client, username, password)

    # Create a notification that is going to be send
    # every time TELL goes up or down by 0.5 USD
    notification_data = {
        'symbol': 'TELL',
        'step': 0.5,
        'title': 'TELL\'s price changed',
        'content': 'TELL\'s price changed',
        'exchange': 'XNAS',
        'type': 'em',
        'is_active': True,
    }

    response = client.post(
        reverse('pricestepnotification-list'), notification_data, format='json'
    )

    assert response.status_code == status.HTTP_201_CREATED
    data_got = json.loads(response.content)
    notification = PriceStepNotification.objects.first()
    assert notification
    url_want = url_join(
        TEST_SERVER, reverse('pricestepnotification-list'), str(notification.id)
    )
    assert (
        response.status_code == status.HTTP_201_CREATED
        and data_got['step'] == notification_data['step']
        and data_got['title'] == notification_data['title']
        and data_got['type'] == notification_data['type']
        and data_got['is_active'] == notification_data['is_active']
        and data_got['url'] == url_want
    )

    # Retrieve a list of tickers
    response = client.get(reverse('ticker-list'))
    ticker_list = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert ticker_list['results']
    tell = ticker_list['results'][0]

    # Create a note for the TELL ticker
    response = client.post(
        reverse('note-list'),
        {
            'title': 'A very important note',
            'content': 'Important content',
            'ticker': tell['url'],
        },
        format='json',
    )
    note_got = json.loads(response.content)
    assert response.status_code == status.HTTP_201_CREATED
    assert note_got['url']


def set_client_jwt(client, username, password, intention='access'):
    """Retrieves JWT and sets the client's authorization bearer header"""
    intentions = ['access', 'refresh']
    if intention not in intentions:
        raise ValueError('Unsupported intention, available are ' + str(intentions))
    response = client.post(
        reverse('token_obtain_pair'),
        {'username': username, 'password': password},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    credentials = json.loads(response.content)
    for temp_intention in intentions:
        assert credentials[temp_intention]
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + credentials[intention])


def url_join(*args):
    url = reduce(lambda a, b: urllib.parse.urljoin(a, b), args)
    return url if url.endswith('/') else url + '/'
