import rest_framework.exceptions
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as RestValidationError
from .models import (
    User,
    Ticker,
    StepNotification,
    IntervalNotification,
    Note
)
from .serializers import (
    UserSerializer,
    TickerSerializer,
    StepNotificationSerializer,
    IntervalNotificationSerializer,
    CreateStepNotificationSerializer,
    CreateIntervalNotificationSerializer,
    NoteSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get_permissions(self):
        if self.request.method == "POST":
            return []
        return super().get_permissions()


class TickerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Ticker.objects.all()
    serializer_class = TickerSerializer


class BaseNotificationViewSet(viewsets.ModelViewSet):
    """Base class to be inherited from for Notification endpoints"""
    permission_classes = [IsAuthenticated]

    # default serializer to use
    default_serializer = None

    # pair of action_name:serializer
    serializers = {}

    def get_queryset(self):
        objects = self.get_notification_class().objects.all()
        return objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer)

    def get_notification_class(self):
        """Has to return the concrete subclass of the Notification model"""
        pass

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = self.get_notification_class().save_notification(serializer)
            Serializer = self.default_serializer
            serializer = Serializer(
                notification, context={"request": request}
            )
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except ValidationError as ex:
            raise RestValidationError(detail=ex.message)


class StepNotificationViewSet(BaseNotificationViewSet):
    default_serializer = StepNotificationSerializer
    serializers = {
        "create": CreateStepNotificationSerializer
    }

    def get_notification_class(self):
        return StepNotification


class IntervalNotificationViewSet(BaseNotificationViewSet):
    default_serializer = IntervalNotificationSerializer
    serializers = {
        "create": CreateIntervalNotificationSerializer
    }

    def get_notification_class(self):
        return IntervalNotification


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.all().filter(user=self.request.user)
