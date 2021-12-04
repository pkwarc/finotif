import logging
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
    SaveStepNotificationSerializer,
    NoteSerializer,
)
from .schemas import AppSchema

_logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get_permissions(self):
        if self.request.method == 'POST':
            return []
        return super().get_permissions()


class TickerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TickerSerializer

    def get_queryset(self):
        return Ticker.objects.filter(stepnotification__user_id=self.request.user)


class StepNotificationViewSet(viewsets.ModelViewSet):
    schema = AppSchema()
    permission_classes = [IsAuthenticated]
    default_serializer = StepNotificationSerializer
    serializers = {
        'create': SaveStepNotificationSerializer,
        'update': SaveStepNotificationSerializer,
    }
    # disable patch
    http_method_names = ['get', 'post', 'head', 'put']
    status_codes = {
        'create': status.HTTP_201_CREATED,
        'update': status.HTTP_200_OK
    }

    def get_queryset(self):
        return StepNotification.objects.all().filter(user=self.request.user)

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer)

    def get_status_code(self):
        return self.status_codes.get(self.action, status.HTTP_200_OK)

    def save(self, request, pk=None):
        data = request.data
        if pk:
            data['pk'] = pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = StepNotification.save_notification(serializer)
            serializer = StepNotificationSerializer(
                notification, context={'request': request}
            )
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=self.get_status_code(),
                headers=headers
            )
        except ValidationError as ex:
            raise RestValidationError(ex.message)

    def create(self, request, *args, **kwargs):
        return self.save(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self.save(request, kwargs['pk'])


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.all().filter(user=self.request.user)
