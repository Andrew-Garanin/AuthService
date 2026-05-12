"""
URL configuration for AuthService project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class IndexView(APIView):
    """Главная страница со списком всех API эндпоинтов. Для удобного доступа к эндпоинтам"""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.utils import timezone
        api_endpoints = [
            {
                'group': 'Аутентификация',
                'endpoints': [
                    {'method': 'POST', 'method_class': 'POST', 'path': '/api/auth/register/', 'desc': 'Регистрация', 'auth': False},
                    {'method': 'POST', 'method_class': 'POST', 'path': '/api/auth/login/', 'desc': 'Вход', 'auth': False},
                    {'method': 'POST', 'method_class': 'POST', 'path': '/api/auth/logout/', 'desc': 'Выход', 'auth': True},
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/auth/profile/', 'desc': 'Профиль (GET)', 'auth': True},
                    {'method': 'PUT', 'method_class': 'PUT', 'path': '/api/auth/profile/', 'desc': 'Профиль (PUT)', 'auth': True},
                    {'method': 'POST', 'method_class': 'POST', 'path': '/api/auth/profile/password/', 'desc': 'Смена пароля', 'auth': True},
                    {'method': 'DELETE', 'method_class': 'DELETE', 'path': '/api/auth/profile/delete/', 'desc': 'Удаление аккаунта', 'auth': True},
                ]
            },
            {
                'group': 'Управление правами (Admin)',
                'endpoints': [
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/admin/roles/', 'desc': 'Список ролей', 'auth': True},
                    {'method': 'POST', 'method_class': 'POST', 'path': '/api/admin/roles/', 'desc': 'Создать роль', 'auth': True},
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/admin/permissions/', 'desc': 'Список прав', 'auth': True},
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/admin/users/USER_ID/roles/', 'desc': 'Роли пользователя', 'auth': True},
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/admin/acl/', 'desc': 'Список ACL', 'auth': True},
                ]
            },
            {
                'group': 'Mock-ресурсы (ещё не готово)',
                'endpoints': [
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/documents/', 'desc': 'Документы', 'auth': True},
                    {'method': 'GET', 'method_class': 'GET', 'path': '/api/tasks/', 'desc': 'Задачи', 'auth': True},
                ]
            },
        ]
        response = render(request, 'auth_api/index.html', {'endpoints': api_endpoints})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('auth_api.urls')),
]
