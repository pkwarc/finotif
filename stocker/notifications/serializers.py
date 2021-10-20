from rest_framework import (
    serializers,
)
from .models import (
    User,
    Ticker,
    PriceStepNotification,
    Note
)


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'url', 'username', 'email', 'password']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True, 'min_length': 6}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class TickerSerializer(serializers.HyperlinkedModelSerializer):
    notes = serializers.HyperlinkedRelatedField(
        view_name='note-detail',
        many=True,
        read_only=True
    )

    class Meta:
        model = Ticker
        fields = ['id', 'url', 'symbol', 'short_name', 'name', 'description', 'notes']


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
        extra_kwargs = {
            'is_active': {'required': True},
            'type': {'required': True}
        }


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Note
        fields = ['id', 'url', 'title', 'content', 'ticker', 'created_at',
                  'modified_at', 'user']
