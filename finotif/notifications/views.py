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
    Note
)
from .serializers import (
    UserSerializer,
    TickerSerializer,
    StepNotificationSerializer,
    CreateStepNotificationSerializer,
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


class StepNotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    default_serializer = StepNotificationSerializer
    serializers = {
        "create": CreateStepNotificationSerializer,
    }

    def get_queryset(self):
        return StepNotification.objects.all().filter(user=self.request.user)

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = StepNotification.save_notification(serializer)
            serializer = StepNotificationSerializer(
                notification, context={"request": request}
            )
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except ValidationError as ex:
            raise RestValidationError(ex.message)


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.all().filter(user=self.request.user)
