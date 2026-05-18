from rest_framework import status
from auth_api.tests.base import AuthAPITestCase


class TestMockResources(AuthAPITestCase):
    """Тесты Mock бизнес-объектов (Documents и Tasks)."""

    def setUp(self):
        super().setUp()
        self.login_as('test_admin@example.com')

    def test_documents_list(self):
        """Получение списка документов."""
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) > 0)

    def test_documents_create(self):
        """Создание документа."""
        data = {'title': 'Test Document', 'description': 'Test Desc'}
        response = self.client.post('/api/documents/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Document')
        self.assertIn('id', response.data)

    def test_documents_detail(self):
        """Получение детальной информации о документе."""
        response = self.client.get('/api/documents/doc-001/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 'doc-001')

    def test_documents_not_found(self):
        """Документ не найден - 404."""
        response = self.client.get('/api/documents/nonexistent/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tasks_list(self):
        """Получение списка задач."""
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) > 0)

    def test_tasks_create(self):
        """Создание задачи."""
        data = {'title': 'Test Task', 'description': 'Test Desc'}
        response = self.client.post('/api/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Task')
        self.assertIn('id', response.data)

    def test_tasks_detail(self):
        """Получение детальной информации о задаче."""
        response = self.client.get('/api/tasks/task-001/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 'task-001')
