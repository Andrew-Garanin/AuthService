from django.shortcuts import render
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, SAFE_METHODS
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, RoleSerializer, PermissionSerializer,
    UserRoleSerializer, PermissionsOverrideSerializer,
    DocumentSerializer, TaskSerializer
)
from .models import Role, Permission, UserRole, RolePermission, PermissionsOverride
from .permissions import (
    RBACPermission,
    DocumentViewPermission, DocumentCreatePermission, DocumentUpdatePermission, DocumentDeletePermission,
    TaskViewPermission, TaskCreatePermission, TaskUpdatePermission, TaskDeletePermission
)

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
    
    def get_permissions(self):
        return [RBACPermission(resource='users', action='manage')]

    def get_queryset(self):
        return Role.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class PermissionViewSet(generics.ListAPIView):
    """Список прав (Admin-only)."""
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        return [RBACPermission(resource='users', action='manage')]

    def get_queryset(self):
        return Permission.objects.all()


class UserRoleViewSet(generics.ListCreateAPIView):
    """Назначение ролей пользователям (Admin-only)."""
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        return [RBACPermission(resource='users', action='manage')]

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
    
    def get_permissions(self):
        return [RBACPermission(resource='acl', action='manage')]

    def get_queryset(self):
        return PermissionsOverride.objects.all()

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


# --- Mock Views ---


class MockDocumentListCreateView(views.APIView):
    """Mock-представление для списка документов (создание/просмотр)."""
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Возвращает список permission классов в зависимости от метода."""
        if self.request.method in SAFE_METHODS:
            return [DocumentViewPermission()]
        elif self.request.method == 'POST':
            return [DocumentCreatePermission()]
        return [IsAuthenticated()]
    
    def get(self, request):
        """Возвращает список mock-документов."""
        # Mock-данные
        documents = [
            {
                'id': 'doc-001',
                'title': 'Политика безопасности',
                'description': 'Документ с правилами безопасности',
                'owner': 'admin@example.com',
                'created_at': '2026-05-01T10:00:00Z',
                'updated_at': '2026-05-10T15:30:00Z',
                'is_public': True
            },
            {
                'id': 'doc-002',
                'title': 'Отчёт за Q1 2026',
                'description': 'Финансовый отчёт',
                'owner': 'manager@example.com',
                'created_at': '2026-05-05T09:00:00Z',
                'updated_at': '2026-05-12T11:00:00Z',
                'is_public': False
            },
            {
                'id': 'doc-003',
                'title': 'Инструкция для сотрудников',
                'description': 'Руководство по работе',
                'owner': 'admin@example.com',
                'created_at': '2026-05-08T14:00:00Z',
                'updated_at': '2026-05-12T16:00:00Z',
                'is_public': True
            }
        ]
        return Response(documents, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Создаёт новый документ (mock)."""
        serializer = DocumentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Mock-создание
        doc_data = serializer.save()
        doc_data['id'] = f'doc-{len(doc_data.get("title", ""))}'
        doc_data['owner'] = request.user.email
        doc_data['created_at'] = timezone.now().isoformat()
        doc_data['updated_at'] = timezone.now().isoformat()
        
        return Response(doc_data, status=status.HTTP_201_CREATED)


class MockDocumentDetailView(views.APIView):
    """Mock-представление для детального просмотра документа."""
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [DocumentViewPermission()]
        elif self.request.method == 'PUT':
            return [DocumentUpdatePermission()]
        elif self.request.method == 'DELETE':
            return [DocumentDeletePermission()]
        return [IsAuthenticated()]
    
    def get(self, request, document_id):
        """Возвращает документ по ID."""
        # Mock-данные
        documents = {
            'doc-001': {
                'id': 'doc-001',
                'title': 'Политика безопасности',
                'description': 'Документ с правилами безопасности',
                'content': 'Полное содержание документа...',
                'owner': 'admin@example.com',
                'created_at': '2026-05-01T10:00:00Z',
                'updated_at': '2026-05-10T15:30:00Z',
                'is_public': True
            },
            'doc-002': {
                'id': 'doc-002',
                'title': 'Отчёт за Q1 2026',
                'description': 'Финансовый отчёт',
                'content': 'Полное содержание документа...',
                'owner': 'manager@example.com',
                'created_at': '2026-05-05T09:00:00Z',
                'updated_at': '2026-05-12T11:00:00Z',
                'is_public': False
            }
        }
        
        if document_id not in documents:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(documents[document_id], status=status.HTTP_200_OK)
    
    def put(self, request, document_id):
        """Обновляет документ (mock)."""
        serializer = DocumentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'id': document_id,
            'message': 'Document updated (mock)',
            **serializer.validated_data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, document_id):
        """Удаляет документ (mock)."""
        return Response({
            'message': f'Document {document_id} deleted (mock)'
        }, status=status.HTTP_200_OK)


class MockTaskListCreateView(views.APIView):
    """Mock-представление для списка задач (создание/просмотр)."""
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [TaskViewPermission()]
        elif self.request.method == 'POST':
            return [TaskCreatePermission()]
        return [IsAuthenticated()]
    
    def get(self, request):
        """Возвращает список mock-задач."""
        tasks = [
            {
                'id': 'task-001',
                'title': 'Обновить документацию',
                'description': 'Актуализировать API docs',
                'status': 'in_progress',
                'priority': 'high',
                'assignee': 'user@example.com',
                'owner': 'manager@example.com',
                'created_at': '2026-05-10T09:00:00Z',
                'updated_at': '2026-05-12T10:00:00Z'
            },
            {
                'id': 'task-002',
                'title': 'Ревью кода',
                'description': 'Проверить Pull Request #42',
                'status': 'pending',
                'priority': 'medium',
                'assignee': '',
                'owner': 'admin@example.com',
                'created_at': '2026-05-11T14:00:00Z',
                'updated_at': '2026-05-11T14:00:00Z'
            },
            {
                'id': 'task-003',
                'title': 'Тестирование системы',
                'description': 'Написать интеграционные тесты',
                'status': 'completed',
                'priority': 'low',
                'assignee': 'user@example.com',
                'owner': 'manager@example.com',
                'created_at': '2026-05-08T11:00:00Z',
                'updated_at': '2026-05-12T16:00:00Z'
            }
        ]
        return Response(tasks, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Создаёт новую задачу (mock)."""
        serializer = TaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        task_data = serializer.save()
        task_data['id'] = f'task-{len(task_data.get("title", ""))}'
        task_data['owner'] = request.user.email
        task_data['created_at'] = timezone.now().isoformat()
        task_data['updated_at'] = timezone.now().isoformat()
        
        return Response(task_data, status=status.HTTP_201_CREATED)


class MockTaskDetailView(views.APIView):
    """Mock-представление для детального просмотра задачи."""
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [TaskViewPermission()]
        elif self.request.method == 'PUT':
            return [TaskUpdatePermission()]
        elif self.request.method == 'DELETE':
            return [TaskDeletePermission()]
        return [IsAuthenticated()]
    
    def get(self, request, task_id):
        """Возвращает задачу по ID."""
        tasks = {
            'task-001': {
                'id': 'task-001',
                'title': 'Обновить документацию',
                'description': 'Актуализировать API docs',
                'status': 'in_progress',
                'priority': 'high',
                'assignee': 'user@example.com',
                'owner': 'manager@example.com',
                'created_at': '2026-05-10T09:00:00Z',
                'updated_at': '2026-05-12T10:00:00Z'
            },
            'task-002': {
                'id': 'task-002',
                'title': 'Ревью кода',
                'description': 'Проверить Pull Request #42',
                'status': 'pending',
                'priority': 'medium',
                'assignee': '',
                'owner': 'admin@example.com',
                'created_at': '2026-05-11T14:00:00Z',
                'updated_at': '2026-05-11T14:00:00Z'
            }
        }
        
        if task_id not in tasks:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(tasks[task_id], status=status.HTTP_200_OK)
    
    def put(self, request, task_id):
        """Обновляет задачу (mock)."""
        serializer = TaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'id': task_id,
            'message': 'Task updated (mock)',
            **serializer.validated_data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, task_id):
        """Удаляет задачу (mock)."""
        return Response({
            'message': f'Task {task_id} deleted (mock)'
        }, status=status.HTTP_200_OK)

