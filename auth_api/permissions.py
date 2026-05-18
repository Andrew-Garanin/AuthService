from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class RBACPermission(BasePermission):
    """
    Кастомный permission для проверки прав на основе RBAC+ACL.
    
    Приоритет проверки:
    1. PermissionsOverride (deny) → 403 Forbidden
    2. PermissionsOverride (grant) → доступ разрешён
    3. RolePermissions → права через роли
    4. Superuser → доступ разрешён
    5. Не аутентифицирован → 401 Unauthorized
    """
    
    # Маппинг методов HTTP к действиям
    method_action_map = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }
    
    # Маппинг ресурсов к кодам прав
    resource_codename_map = {
        'documents': 'documents_{}',
        'tasks': 'tasks_{}',
        'users': 'users_{}',
        'roles': 'users_{}',  # Роли через users_manage
        'permissions': 'users_{}',
        'acl': 'acl_{}',
    }
    
    def __init__(self, resource=None, action=None):
        """
        Инициализация permission.
        
        :param resource: Тип ресурса (documents, tasks, users, acl)
        :param action: Действие (view, create, update, delete, manage)
        """
        self.resource = resource
        self.action = action
    
    def has_permission(self, request, view):
        # Не аутентифицирован → 401
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser → доступ разрешён
        if request.user.is_superuser:
            return True
        
        # Определяем действие из метода
        action = self.action or self.method_action_map.get(request.method, 'view')
        
        # Определяем ресурс из URL или view
        resource = self._get_resource(request, view)
        
        if not resource:
            # Если ресурс не определён, разрешаем доступ (для общих эндпоинтов)
            return True
        
        # Проверяем PermissionsOverride (deny)
        if self._has_override(request.user, resource, action, action_type='deny'):
            return False
        
        # Проверяем PermissionsOverride (grant)
        if self._has_override(request.user, resource, action, action_type='grant'):
            return True
        
        # Проверяем RolePermissions
        if self._has_role_permission(request.user, resource, action):
            return True
        
        # Не найдено → 403
        return False
    
    def _get_resource(self, request, view):
        """Определяет тип ресурса из URL или view."""
        if self.resource:
            return self.resource
        
        # Пытаемся определить из URL
        path = request.path.lower()
        if '/documents/' in path:
            return 'documents'
        elif '/tasks/' in path:
            return 'tasks'
        elif '/users/' in path or '/roles/' in path or '/permissions/' in path:
            return 'users'
        elif '/acl/' in path:
            return 'acl'
        elif '/profile/' in path:
            return 'users'  # Профиль = пользователи
        
        return None
    
    def _has_override(self, user, resource, action, action_type, view=None):
        """
        Проверяет наличие переопределения прав (ACL).
        
        :param user: Пользователь
        :param resource: Тип ресурса
        :param action: Действие
        :param action_type: 'grant' или 'deny'
        :param view: View объект (для получения kwargs)
        """
        from .models import PermissionsOverride
        
        codename = self.resource_codename_map.get(resource, '{}').format(action)
        
        # Ищем переопределения для этого пользователя или общие (user=None)
        overrides = PermissionsOverride.objects.filter(
            action_type=action_type,
            permission__codename=codename,
            resource_type=resource
        ).filter(
            user=user
        )
        
        # Добавляем общие переопределения (user=None)
        general_overrides = PermissionsOverride.objects.filter(
            action_type=action_type,
            permission__codename=codename,
            resource_type=resource,
            user=None
        )
        overrides = overrides | general_overrides
        
        # Также проверяем переопределения для конкретного ресурса
        # (если resource_id указан в запросе)
        if view:
            resource_id = getattr(view, 'kwargs', {}).get('pk') or \
                          getattr(view, 'kwargs', {}).get('document_id') or \
                          getattr(view, 'kwargs', {}).get('task_id')
            
            if resource_id:
                specific_overrides = PermissionsOverride.objects.filter(
                    action_type=action_type,
                    permission__codename=codename,
                    resource_type=resource,
                    resource_id=str(resource_id)
                ).filter(
                    user=user
                )
                general_specific = PermissionsOverride.objects.filter(
                    action_type=action_type,
                    permission__codename=codename,
                    resource_type=resource,
                    resource_id=str(resource_id),
                    user=None
                )
                overrides = overrides | specific_overrides | general_specific
        
        return overrides.exists()
    
    def _has_role_permission(self, user, resource, action):
        """
        Проверяет наличие права через роли пользователя.
        
        :param user: Пользователь
        :param resource: Тип ресурса
        :param action: Действие
        """
        from .models import UserRole, RolePermission
        
        # Получаем все роли пользователя
        user_roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
        
        if not user_roles:
            return False
        
        # Формируем код права
        codename = self.resource_codename_map.get(resource, '{}').format(action)
        
        # Для action='manage' также проверяем базовые права
        if action == 'manage':
            # Проверяем users_manage для пользователей
            if resource == 'users':
                codename = 'users_manage'
            elif resource == 'acl':
                codename = 'acl_manage'
        
        # Проверяем есть ли такое право у любой из ролей
        return RolePermission.objects.filter(
            role_id__in=user_roles,
            permission__codename=codename
        ).exists()


# Convenience классы для часто используемых проверок
class DocumentViewPermission(RBACPermission):
    """Просмотр документов."""
    def __init__(self):
        super().__init__(resource='documents', action='view')


class DocumentCreatePermission(RBACPermission):
    """Создание документов."""
    def __init__(self):
        super().__init__(resource='documents', action='create')


class DocumentUpdatePermission(RBACPermission):
    """Обновление документов."""
    def __init__(self):
        super().__init__(resource='documents', action='update')


class DocumentDeletePermission(RBACPermission):
    """Удаление документов."""
    def __init__(self):
        super().__init__(resource='documents', action='delete')


class TaskViewPermission(RBACPermission):
    """Просмотр задач."""
    def __init__(self):
        super().__init__(resource='tasks', action='view')


class TaskCreatePermission(RBACPermission):
    """Создание задач."""
    def __init__(self):
        super().__init__(resource='tasks', action='create')


class TaskUpdatePermission(RBACPermission):
    """Обновление задач."""
    def __init__(self):
        super().__init__(resource='tasks', action='update')


class TaskDeletePermission(RBACPermission):
    """Удаление задач."""
    def __init__(self):
        super().__init__(resource='tasks', action='delete')
