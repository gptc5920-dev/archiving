from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserListAPIView, UserViewSet


router = DefaultRouter()
router.register("", UserViewSet, basename="account")

urlpatterns = [
    path("users/", UserListAPIView.as_view(), name="user-list"),
    *router.urls,
]
