import json
import logging
import pytest
import urllib.parse
from functools import reduce
from unittest import mock
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ..models import (
    StepNotification,
    TickerProperty,
    NotificationType,
    User,
    Note
)
from ..services import TickerDto

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
        reverse('stepnotification-list'),
    ],
)
def test_if_not_loggedin_then_unauthorized(client, url):
    assert client.get(url).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_healthcheck(client):
    response = client.get('/ht/?format=json')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@mock.patch('finotif.notifications.models.TickerProvider.info')
def test_api_workflow(mock_info, client):
    def user_workflow(username, password, email, info):
        # Mock the call to any external api:
        mock_info.return_value = info
        # User registers
        user_data = {
            'username': username,
            'password': password,
            'email': email,
        }

        response = client.post(reverse('user-list'), user_data, format='json')

        user_details = json.loads(response.content)
        user = User.objects.get(email=email)
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            'password' not in user_details
            and username == user_details['username']
            and email == user_details['email']
        )

        # User signs in (obtains JWT)
        response = client.post(
            reverse('token_obtain_pair'),
            {'username': username, 'password': password},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        credentials = json.loads(response.content)
        token = credentials['access']
        assert token
        assert credentials['refresh']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        # User tries to get their data
        response = client.get(reverse('user-list'), format='json')
        user_list = json.loads(response.content)

        # Ensure users can only get their own data
        assert (
            # has to be exactly one
            len(user_list['results']) == 1
            and user_list['results'][0]['email'] == email
            and user_list['results'][0]['date_joined']
        )

        # User creates a notification that is going to be send
        # every time the security goes up or down by 0.5 USD
        notification_data = {
            'symbol': info.symbol,
            'mic': 'XNAS',
            'change': 0.5,
            'property': TickerProperty.PRICE.name,
            'type': NotificationType.EMAIL.name,
            'title': f'{info.symbol}\'s price changed',
            'content': f'{info.symbol}\'s price changed',
            'is_active': True,
        }

        response = client.post(
            reverse('stepnotification-list'), notification_data, format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        notification = StepNotification.objects.get(user=user)
        expected_url = url_join(
            TEST_SERVER, reverse('stepnotification-list'), str(notification.id)
        )
        data_got = json.loads(response.content)
        assert (
            response.status_code == status.HTTP_201_CREATED
            and data_got['change'] == notification_data['change']
            and data_got['title'] == notification_data['title']
            and data_got['property'] == notification_data['property']
            and data_got['type'] == notification_data['type']
            and data_got['is_active'] == notification_data['is_active']
            and data_got['url'] == expected_url
            and data_got['created_at']
            and data_got['modified_at']
        )

        # User updates the notification
        notification_data['type'] = NotificationType.PUSH.name
        response = client.put(data_got['url'], notification_data, format='json')
        data_got = json.loads(response.content)
        notification = StepNotification.objects.get(pk=data_got['id'])
        assert (
            response.status_code == status.HTTP_200_OK
            and data_got['type'] == notification_data['type']
            and notification.type == NotificationType.PUSH
        )

        # User retrieves the list of tickers
        response = client.get(reverse('ticker-list'))
        ticker_list = json.loads(response.content)
        assert response.status_code == status.HTTP_200_OK
        assert len(ticker_list['results']) == 1
        ticker = ticker_list['results'][0]

        # User creates a note to the ticker
        response = client.post(
            reverse('note-list'),
            {
                'title': 'A very important note',
                'content': 'Important content',
                'ticker': ticker['url'],
            },
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        note_got = json.loads(response.content)
        note = Note.objects.get(user=user)
        expected_url = url_join(
            TEST_SERVER, reverse('note-list'), str(note.id)
        )
        assert (
            note_got['url'] == expected_url
            and note_got['title'] == note.title
            and note_got['content'] == note.content
            and note_got['created_at']
            and note_got['modified_at']
        )

    # Execute the workflow
    # At least two users in order to ensure that
    # no user can access others data
    info = {
        'symbol': 'TELL',
        'name': 'Tellurian Inc.',
        'short_name': 'anything but not blank',
        'description': 'anything but not blank',
        'exchange': 'anything but not blank',
    }
    user_workflow('user0',  'user0Te$tPass', 'user0@email.com', info=TickerDto(**info))
    info.update(symbol='MSFT', name='Microsoft Corporation')
    user_workflow('user1', 'user1Te$tPass', 'user1@email.com', info=TickerDto(**info))
    info.update(symbol='NIO', name='NIO')
    user_workflow('user2', 'user2Te$tPass', 'user2@email.com', info=TickerDto(**info))


def url_join(*args):
    url = reduce(lambda a, b: urllib.parse.urljoin(a, b), args)
    return url if url.endswith('/') else url + '/'
