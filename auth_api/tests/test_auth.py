from rest_framework import status
from auth_api.models import User
from auth_api.tests.base import AuthAPITestCase


class TestRegistration(AuthAPITestCase):
    """Тесты регистрации пользователей."""

    def test_register_success(self):
        """Успешная регистрация."""
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'password_confirm': 'NewPass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email='newuser@example.com').count(), 1)

    def test_register_password_mismatch(self):
        """Пароли не совпадают."""
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123',
            'password_confirm': 'DifferentPass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Email уже существует."""
        data = {
            'email': 'test_admin@example.com',
            'password': 'NewPass123',
            'password_confirm': 'NewPass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestLoginLogout(AuthAPITestCase):
    """Тесты входа и выхода."""

    def test_login_success(self):
        """Успешный вход."""
        data = {'email': 'test_admin@example.com', 'password': 'TestPass123'}
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Неверный пароль."""
        data = {'email': 'test_admin@example.com', 'password': 'WrongPass'}
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Вход неактивного пользователя."""
        self.admin.is_active = False
        self.admin.save()
        data = {'email': 'test_admin@example.com', 'password': 'TestPass123'}
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        """Успешный выход."""
        self.login_as('test_admin@example.com')
        response = self.client.post('/api/auth/logout/', {'refresh_token': 'dummy'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestProfile(AuthAPITestCase):
    """Тесты профиля пользователя."""

    def setUp(self):
        super().setUp()
        self.login_as('test_user@example.com')

    def test_get_profile(self):
        """Получение профиля."""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test_user@example.com')

    def test_update_profile(self):
        """Обновление профиля."""
        data = {
            'email': 'test_user@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        }
        response = self.client.patch('/api/auth/profile/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')

    def test_change_password(self):
        """Смена пароля."""
        data = {
            'old_password': 'TestPass123',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456'
        }
        response = self.client.post('/api/auth/profile/password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login_response = self.client.post('/api/auth/login/', {
            'email': 'test_user@example.com',
            'password': 'NewPass456'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_delete_account(self):
        """Мягкое удаление аккаунта."""
        response = self.client.delete('/api/auth/profile/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(email='test_user@example.com')
        self.assertFalse(user.is_active)

        self.client.credentials()
        login_response = self.client.post('/api/auth/login/', {
            'email': 'test_user@example.com',
            'password': 'TestPass123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)


class TestSessionAuthentication(AuthAPITestCase):
    """Тесты сессионной аутентификации (для браузера)."""

    def test_session_auth_works(self):
        """Сессионная аутентификация работает для API."""
        # Логинимся через API (получаем токен)
        login_response = self.client.post('/api/auth/login/', {
            'email': 'test_user@example.com',
            'password': 'TestPass123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Используем токен для доступа
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + login_response.data['access']
        )

        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test_user@example.com')

    def test_jwt_token_structure(self):
        """JWT-токен содержит правильную структуру."""
        login_response = self.client.post('/api/auth/login/', {
            'email': 'test_admin@example.com',
            'password': 'TestPass123'
        })

        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)

        # Токен состоит из 3 частей (header.payload.signature)
        access_token = login_response.data['access']
        parts = access_token.split('.')
        self.assertEqual(len(parts), 3)
