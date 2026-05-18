from rest_framework import status
from auth_api.tests.base import AuthAPITestCase


class TestRBACPermissions(AuthAPITestCase):
    """Тесты системы разграничения прав доступа (RBAC + ACL)."""

    def test_admin_full_access(self):
        """Admin имеет полный доступ ко всем ресурсам и Admin API."""
        self.login_as('test_admin@example.com')

        # Документы - полный доступ
        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/documents/', {'title': 'Test'}).status_code,
            status.HTTP_201_CREATED
        )

        # Задачи - полный доступ
        self.assertEqual(self.client.get('/api/tasks/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/tasks/', {'title': 'Test'}).status_code,
            status.HTTP_201_CREATED
        )

        # Admin API
        self.assertEqual(self.client.get('/api/admin/roles/').status_code, status.HTTP_200_OK)

    def test_manager_documents_tasks(self):
        """Manager может управлять документами и задачами, но не Admin API."""
        self.login_as('test_manager@example.com')

        # Документы - view, create, update
        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/documents/', {'title': 'Test Doc'}).status_code,
            status.HTTP_201_CREATED
        )

        # Задачи - view, create, update
        self.assertEqual(self.client.get('/api/tasks/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/tasks/', {'title': 'Test Task'}).status_code,
            status.HTTP_201_CREATED
        )

        # Admin API - запрещено
        self.assertEqual(self.client.get('/api/admin/roles/').status_code, status.HTTP_403_FORBIDDEN)

    def test_user_limited_access(self):
        """User может только просматривать документы и создавать задачи."""
        self.login_as('test_user@example.com')

        # Документы - только view
        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/documents/', {'title': 'Test'}).status_code,
            status.HTTP_403_FORBIDDEN
        )

        # Задачи - view, create
        self.assertEqual(self.client.get('/api/tasks/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/tasks/', {'title': 'Test Task'}).status_code,
            status.HTTP_201_CREATED
        )

    def test_guest_view_only(self):
        """Guest может только просматривать документы и задачи."""
        self.login_as('test_guest@example.com')

        # Документы - только view
        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/documents/', {'title': 'Test'}).status_code,
            status.HTTP_403_FORBIDDEN
        )

        # Задачи - только view
        self.assertEqual(self.client.get('/api/tasks/').status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post('/api/tasks/', {'title': 'Test'}).status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_restricted_denied(self):
        """Restricted пользователь не имеет доступа даже к просмотру (ACL deny)."""
        self.login_as('test_restricted@example.com')

        # Документы - запрет через ACL
        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_403_FORBIDDEN)

        # Задачи - запрет через ACL
        self.assertEqual(self.client.get('/api/tasks/').status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_access(self):
        """Неавторизованный доступ возвращает 401."""
        self.client.credentials()

        self.assertEqual(self.client.get('/api/documents/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get('/api/admin/roles/').status_code, status.HTTP_401_UNAUTHORIZED)
