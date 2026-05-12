from django.shortcuts import render
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, RoleSerializer, PermissionSerializer,
    UserRoleSerializer, PermissionsOverrideSerializer
)
from .models import Role, Permission, UserRole, PermissionsOverride

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Назначаем роль User по умолчанию
        default_user_role = Role.objects.filter(name='User').first()
        if default_user_role:
            UserRole.objects.create(user=user, role=default_user_role)

        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Пользователь успешно зарегистрирован'
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    """Вход пользователя."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class LogoutView(views.APIView):
    """Выход пользователя (инвалидация токена)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'refresh_token не указан'}, status=status.HTTP_400_BAD_REQUEST)

            # Пробуем добавить токен в blacklist
            try:
                from rest_framework_simplejwt.token_blacklist.models import TokenBlacklist
                from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRT

                token = SimpleJWTRT(refresh_token)
                TokenBlacklist.from_refresh_token(token)
            except ImportError:
                # Если blacklist не настроен, просто возвращаем успех
                pass
            except Exception:
                # Игнорируем ошибки blacklist
                pass

            return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Ошибка: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Профиль текущего пользователя."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """Смена пароля."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Пароль успешно изменён'}, status=status.HTTP_200_OK)


class DeleteAccountView(generics.DestroyAPIView):
    """Мягкое удаление аккаунта."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.soft_delete()
        return Response({'message': 'Аккаунт успешно удалён'}, status=status.HTTP_200_OK)


# --- Admin Views ---

class RoleViewSet(generics.ListCreateAPIView):
    """CRUD ролей (Admin-only)."""
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Role.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class PermissionViewSet(generics.ListAPIView):
    """Список прав (Admin-only)."""
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Permission.objects.all()


class UserRoleViewSet(generics.ListCreateAPIView):
    """Назначение ролей пользователям (Admin-only)."""
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return UserRole.objects.filter(user_id=user_id)

    def perform_create(self, serializer):
        user_id = self.kwargs.get('user_id')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        serializer.save(user=user, assigned_by=self.request.user)


class PermissionsOverrideViewSet(generics.ListCreateAPIView):
    """Управление переопределениями прав (Admin-only)."""
    serializer_class = PermissionsOverrideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PermissionsOverride.objects.all()

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)

