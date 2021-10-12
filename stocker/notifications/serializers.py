from django.contrib.auth.models import User
from rest_framework import (
    serializers,
)
from .models import (
    Ticker,
    PriceStepNotification,
)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email']


class TickerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ticker
        fields = ['url', 'symbol', 'short_name', 'name', 'description']


class PriceStepNotificationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PriceStepNotification
        fields = ['id', 'url', 'title', 'content', 'ticker', 'type',
                  'is_active', 'step', 'created_at', 'modified_at']


class PriceStepNotificationCreateSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(help_text="The symbol of the ticker")
    exchange = serializers.CharField(help_text='Market Identifier Code (MIC)')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PriceStepNotification
        fields = ['title', 'content', 'is_active', 'type', 'exchange',
                  'symbol', 'step', 'user']
        required_field = True
        extra_kwargs = {
            'is_active': {'required': True},
            'type': {'required': True}
        }
