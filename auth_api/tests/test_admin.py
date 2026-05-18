from rest_framework import status
from auth_api.tests.base import AuthAPITestCase


class TestAdminAPI(AuthAPITestCase):
    """Тесты Admin API (управление ролями, правами, ACL)."""

    def test_admin_can_manage_roles(self):
        """Admin может просматривать и создавать роли."""
        self.login_as('test_admin@example.com')

        response = self.client.get('/api/admin/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post('/api/admin/roles/', {
            'name': 'New Role',
            'description': 'Test role'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_manage_roles(self):
        """Manager не может управлять ролями."""
        self.login_as('test_manager@example.com')

        self.assertEqual(self.client.get('/api/admin/roles/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.post('/api/admin/roles/', {
                'name': 'New Role',
                'description': 'Test role'
            }).status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_admin_can_assign_roles(self):
        """Admin может назначать роли пользователям."""
        self.login_as('test_admin@example.com')

        response = self.client.post(
            f'/api/admin/users/{self.user.id}/roles/',
            {'role': str(self.admin_role.id)}
        )
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_admin_can_manage_acl(self):
        """Admin может просматривать и создавать ACL записи."""
        self.login_as('test_admin@example.com')

        response = self.client.get('/api/admin/acl/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post('/api/admin/acl/', {
            'user': str(self.user.id),
            'permission': str(self.permissions['documents_view'].id),
            'resource_type': 'documents',
            'action_type': 'grant'
        })
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_user_cannot_manage_acl(self):
        """User не может управлять ACL."""
        self.login_as('test_user@example.com')

        self.assertEqual(self.client.get('/api/admin/acl/').status_code, status.HTTP_403_FORBIDDEN)
