from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets

from .serializers import UserCreateSerializer, UserSerializer


User = get_user_model()


class IsAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "list":
            return request.user.is_staff

        return True

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.order_by("id")
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return self.queryset

        if self.request.user.is_authenticated:
            return self.queryset.filter(pk=self.request.user.pk)

        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        return UserSerializer


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
