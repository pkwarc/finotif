"""stocker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from rest_framework.documentation import include_docs_urls
from stocker.notifications.views import (
    UserViewSet,
    StepNotificationViewSet,
    IntervalNotificationViewSet,
    TickerViewSet,
    NoteViewSet
)

router = routers.DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'ticker', TickerViewSet)
router.register(r'stepNotification', StepNotificationViewSet, basename='stepnotification')
router.register(r'intervalNotification', IntervalNotificationViewSet, basename='intervalnotification')
router.register(r'note', NoteViewSet, basename='note')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', include_docs_urls(title='Stocker API'))
]
