from rest_framework import routers
from .views import (
    UserViewSet,
    StepNotificationViewSet,
    TickerViewSet,
    NoteViewSet,
)

router = routers.DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'ticker', TickerViewSet, basename='ticker')
router.register(r'stepNotification', StepNotificationViewSet, basename='stepnotification')
router.register(r'note', NoteViewSet, basename='note')
