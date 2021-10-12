from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import (
    viewsets,
    status
)
from .models import (
    Ticker,
    PriceStepNotification,
)
from .serializers import (
    UserSerializer,
    TickerSerializer,
    PriceStepNotificationSerializer,
    PriceStepNotificationCreateSerializer
)
from .services import create_price_step_notification


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TickerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticker.objects.all()
    serializer_class = TickerSerializer


class PriceStepNotificationViewSet(viewsets.ModelViewSet):
    queryset = PriceStepNotification.objects.all()

    default_serializer = PriceStepNotificationSerializer
    serializers = {
        'create': PriceStepNotificationCreateSerializer,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = create_price_step_notification(serializer.data)
        serializer = PriceStepNotificationSerializer(notification, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


