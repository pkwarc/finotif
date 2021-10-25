from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import User, Ticker, PriceStepNotification, Note
from .serializers import (
    UserSerializer,
    TickerSerializer,
    PriceStepNotificationSerializer,
    PriceStepNotificationCreateSerializer,
    NoteSerializer,
)
from .services import create_price_step_notification


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


class PriceStepNotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    default_serializer = PriceStepNotificationSerializer
    serializers = {
        "create": PriceStepNotificationCreateSerializer,
    }

    def get_queryset(self):
        return PriceStepNotification.objects.all().filter(user=self.request.user)

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = create_price_step_notification(user=request.user, data=serializer.data)
        serializer = PriceStepNotificationSerializer(
            notification, context={"request": request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.all().filter(user=self.request.user)
