from django.test import TestCase
from rest_framework.test import APIClient
from auth_api.models import User, Role, Permission, UserRole, RolePermission, PermissionsOverride


class AuthAPITestCase(TestCase):
    """Базовый класс для тестов с настройкой клиентов."""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных один раз для всех тестов."""
        cls.admin_role = Role.objects.create(name='Test Admin')
        cls.manager_role = Role.objects.create(name='Test Manager')
        cls.user_role = Role.objects.create(name='Test User')
        cls.guest_role = Role.objects.create(name='Test Guest')

        cls.permissions = {
            'documents_view': Permission.objects.create(
                name='View Documents', codename='documents_view',
                resource='documents', action='view'
            ),
            'documents_create': Permission.objects.create(
                name='Create Documents', codename='documents_create',
                resource='documents', action='create'
            ),
            'documents_update': Permission.objects.create(
                name='Update Documents', codename='documents_update',
                resource='documents', action='update'
            ),
            'documents_delete': Permission.objects.create(
                name='Delete Documents', codename='documents_delete',
                resource='documents', action='delete'
            ),
            'tasks_view': Permission.objects.create(
                name='View Tasks', codename='tasks_view',
                resource='tasks', action='view'
            ),
            'tasks_create': Permission.objects.create(
                name='Create Tasks', codename='tasks_create',
                resource='tasks', action='create'
            ),
            'tasks_update': Permission.objects.create(
                name='Update Tasks', codename='tasks_update',
                resource='tasks', action='update'
            ),
            'tasks_delete': Permission.objects.create(
                name='Delete Tasks', codename='tasks_delete',
                resource='tasks', action='delete'
            ),
            'users_manage': Permission.objects.create(
                name='Manage Users', codename='users_manage',
                resource='users', action='manage'
            ),
            'acl_manage': Permission.objects.create(
                name='Manage ACL', codename='acl_manage',
                resource='acl', action='manage'
            ),
        }

        # Admin - все права
        for perm in cls.permissions.values():
            RolePermission.objects.create(role=cls.admin_role, permission=perm)

        # Manager - документы (view, create, update), задачи (view, create, update)
        for codename in ['documents_view', 'documents_create', 'documents_update',
                         'tasks_view', 'tasks_create', 'tasks_update']:
            RolePermission.objects.create(
                role=cls.manager_role,
                permission=cls.permissions[codename]
            )

        # User - документы (view), задачи (view, create)
        for codename in ['documents_view', 'tasks_view', 'tasks_create']:
            RolePermission.objects.create(
                role=cls.user_role,
                permission=cls.permissions[codename]
            )

        # Guest - документы (view), задачи (view)
        for codename in ['documents_view', 'tasks_view']:
            RolePermission.objects.create(
                role=cls.guest_role,
                permission=cls.permissions[codename]
            )

        # Пользователи
        cls.admin = User.objects.create_superuser(
            email='test_admin@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='Admin'
        )
        UserRole.objects.create(user=cls.admin, role=cls.admin_role)

        cls.manager = User.objects.create_user(
            email='test_manager@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='Manager'
        )
        UserRole.objects.create(user=cls.manager, role=cls.manager_role)

        cls.user = User.objects.create_user(
            email='test_user@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='User'
        )
        UserRole.objects.create(user=cls.user, role=cls.user_role)

        cls.guest = User.objects.create_user(
            email='test_guest@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='Guest'
        )
        UserRole.objects.create(user=cls.guest, role=cls.guest_role)

        cls.restricted = User.objects.create_user(
            email='test_restricted@example.com',
            password='TestPass123',
            first_name='Test',
            last_name='Restricted'
        )
        UserRole.objects.create(user=cls.restricted, role=cls.guest_role)

        # ACL deny для restricted
        PermissionsOverride.objects.create(
            user=cls.restricted,
            permission=cls.permissions['documents_view'],
            resource_type='documents',
            action_type='deny'
        )
        PermissionsOverride.objects.create(
            user=cls.restricted,
            permission=cls.permissions['tasks_view'],
            resource_type='tasks',
            action_type='deny'
        )

    def setUp(self):
        """Создание API клиента перед каждым тестом."""
        self.client = APIClient()

    def login_as(self, email):
        """Вход под пользователем и установка токена."""
        response = self.client.post('/api/auth/login/', {
            'email': email,
            'password': 'TestPass123'
        })
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + response.data['access']
        )
