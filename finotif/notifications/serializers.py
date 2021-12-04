from rest_framework import (
    serializers,
)
from .models import (
    User,
    Ticker,
    StepNotification,
    Note,
    NotificationType,
    TickerProperty,
)


class DisplayIntChoiceField(serializers.ChoiceField):
    """Allows the api client to use fields of the type IntegerChoices as strings"""
    def __init__(self, choices, **kwargs):
        super().__init__(choices, **kwargs)
        self.label_value = {
            label: value for value, label in self.choices.items()
        }

    def to_internal_value(self, data):
        if data == '' and self.allow_blank:
            return ''
        try:
            return self.label_value[str(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        if value in ('', None):
            return value
        return self.choices.get(int(value), value)


class PkDefault:
    requires_context = True

    def __call__(self, serializer_field):
        request_data = serializer_field.context['request'].data
        return request_data.get('pk', None)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'url', 'username', 'email',
                  'password', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'email': {'required': True},
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


class StepNotificationSerializer(serializers.HyperlinkedModelSerializer):
    property = DisplayIntChoiceField(TickerProperty.choices)
    type = DisplayIntChoiceField(NotificationType.choices)

    class Meta:
        model = StepNotification
        read_only_fields = ['created_at', 'modified_at']
        fields = ['id', 'url', 'title', 'content', 'ticker', 'type',
                  'is_active', 'property', 'change', 'created_at', 'modified_at']


class SaveStepNotificationSerializer(serializers.ModelSerializer):
    property = DisplayIntChoiceField(TickerProperty.choices)
    type = DisplayIntChoiceField(NotificationType.choices)
    symbol = serializers.CharField(help_text="The symbol of the ticker")
    mic = serializers.CharField(help_text='Market Identifier Code (MIC)')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    pk = serializers.HiddenField(default=PkDefault())

    class Meta:
        model = StepNotification
        fields = ['pk', 'symbol', 'mic', 'title', 'content', 'is_active',
                  'type', 'property', 'change', 'user']
        read_only_fields = ['created_at', 'modified_at']
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
