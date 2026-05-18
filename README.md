# Система аутентификации и авторизации (DRF + Postgres)

На главной странице для удобства тестирования добавлены все эндпоинты.

## Описание архитектуры

Приложение реализует систему управления доступом на основе гибридной модели **RBAC (Role-Based Access Control)** + **ACL (Access Control List)**.

---

## Схема базы данных

### 1. Модель `User` (auth_api.User)
Кастомная модель пользователя с email-аутентификацией.

| Поле | Тип | Описание                                    |
|------|-----|---------------------------------------------|
| `id` | UUID | Первичный ключ                              |
| `email` | Email | Уникальный email для входа                  |
| `first_name` | Char(150) | Имя                                         |
| `last_name` | Char(150) | Фамилия                                     |
| `middle_name` | Char(150) | Отчество (опционально)                      |
| `is_active` | Boolean | Статус активности (мягкое удаление = False) |
| `is_staff` | Boolean | Доступ в админку                            |
| `is_superuser` | Boolean | Суперпользователь                           |
| `date_joined` | DateTime | Дата регистрации                            |

### 2. Модель `Role`
Роль пользователя — группа прав.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `name` | Char(100) | Название роли |
| `description` | Text | Описание роли |
| `created_at` | DateTime | Дата создания |

**Стандартные роли:**
- `Admin` — полный доступ ко всем ресурсам
- `Manager` — управление контентом (документы, задачи)
- `User` — базовые права (просмотр, создание своих ресурсов)
- `Guest` — только просмотр

### 3. Модель `Permission`
Атомарное право доступа.

| Поле | Тип | Описание                                                  |
|------|-----|-----------------------------------------------------------|
| `id` | UUID | Первичный ключ                                            |
| `name` | Char(200) | Название                                                  |
| `codename` | Char(100) | Уникальный код (например, `documents_view`)               |
| `resource` | Char(100) | Тип ресурса (`documents`, `tasks`, `users`, `acl`)        |
| `action` | Char(50) | Действие (`view`, `create`, `update`, `delete`, `manage`) |
| `description` | Text | Описание                                                  |
| `created_at` | DateTime | Дата создания                                             |

**Примеры прав:**
- `documents_view` — просмотр документов
- `documents_create` — создание документов
- `documents_update` — редактирование документов
- `documents_delete` — удаление документов
- `tasks_view`, `tasks_create`, `tasks_update`, `tasks_delete`
- `users_view`, `users_manage`
- `acl_manage` — управление переопределениями прав

### 4. Модель `UserRole`
Связь пользователя с ролью.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `user` | FK → User | Пользователь |
| `role` | FK → Role | Роль |
| `assigned_at` | DateTime | Дата назначения |
| `assigned_by` | FK → User | Кто назначил |


### 5. Модель `RolePermission`
Связь роли с правами.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `role` | FK → Role | Роль |
| `permission` | FK → Permission | Право |
| `granted_at` | DateTime | Дата выдачи |


### 6. Модель `PermissionsOverride`
Явное переопределение прав для конкретного пользователя на ресурс (ACL).

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `user` | FK → User (nullable) | Пользователь (если null — применяется ко всем) |
| `resource_type` | Char(50) | Тип ресурса (`documents`, `tasks`, `users`, `custom`) |
| `resource_id` | Char(100) | ID конкретного ресурса (пусто — для всех ресурсов типа) |
| `permission` | FK → Permission | Право |
| `action_type` | Char(10) | `grant` (разрешить) или `deny` (запретить) |
| `description` | Text | Описание |
| `granted_by` | FK → User | Кто выдал |
| `created_at` | DateTime | Дата создания |
| `expires_at` | DateTime (nullable) | Дата истечения действия |


## Приоритет проверки прав

При запросе к ресурсу система проверяет права в следующем порядке:

1. **PermissionsOverride (deny)** — если есть явный запрет для пользователя → **403 Forbidden**
2. **PermissionsOverride (grant)** — если есть явное разрешение → **доступ разрешён**
3. **RolePermissions** — права через роли пользователя
4. **Superuser** — если `is_superuser=True` → **доступ разрешён**
5. Если пользователь не аутентифицирован → **401 Unauthorized**

---

## Аутентификация

Приложение поддерживает **два механизма аутентификации**:

### 1. JWT-токены (основной для API)

**Как работает:**
1. Пользователь отправляет `email` + `password` на `/api/auth/login/`
2. Сервер проверяет данные и возвращает пару токенов:
   - `access` — короткоживущий (1 час), используется для доступа к API
   - `refresh` — долгоживущий (7 дней), используется для обновления access
3. Клиент сохраняет токены (localStorage/cookies)
4. При каждом запросе клиент отправляет заголовок:
   ```
   Authorization: Bearer <access_token>
   ```
5. Сервер **не хранит состояние сессии** — проверяет подпись токена


### 2. Django Sessions (для админки)

**Как работает:**
1. Пользователь логинится через HTML-форму
2. Сервер создаёт запись в таблице `django_session`
3. Сервер устанавливает cookie `sessionid` в браузере
4. При каждом запросе браузер автоматически отправляет cookie
5. Сервер ищет `sessionid` в базе и восстанавливает пользователя

- **API endpoints** (`/api/*`) — используют JWT (`Authorization: Bearer`)
- **Django Admin** (`/admin/`) — использует сессии (cookie `sessionid`)
- **HTML-шаблоны** (`/`) — могут использовать оба метода

---

## API Endpoints

### Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| GET | `/api/auth/profile/` | Профиль текущего пользователя |
| PUT | `/api/auth/profile/` | Обновление профиля |
| POST | `/api/auth/profile/password/` | Смена пароля |
| DELETE | `/api/auth/profile/delete/` | Мягкое удаление аккаунта |

### Управление правами (Admin-only)
| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/api/admin/roles/` | CRUD ролей |
| GET | `/api/admin/permissions/` | Список прав |
| GET/POST | `/api/admin/users/<user_id>/roles/` | Назначение ролей пользователю |
| GET/POST | `/api/admin/acl/` | Управление переопределениями прав |

### Ресурсы (Mock - без БД)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/documents/` | Список документов |
| POST | `/api/documents/` | Создание документа |
| GET | `/api/documents/<id>/` | Детали документа |
| PUT | `/api/documents/<id>/` | Обновление документа |
| DELETE | `/api/documents/<id>/` | Удаление документа |
| GET | `/api/tasks/` | Список задач |
| POST | `/api/tasks/` | Создание задачи |
| GET | `/api/tasks/<id>/` | Детали задачи |
| PUT | `/api/tasks/<id>/` | Обновление задачи |
| DELETE | `/api/tasks/<id>/` | Удаление задачи |

---

## Тестирование системы прав

### Тестовые пользователи

После загрузки `initial_data.json` и запуска `create_test_users` доступны:

| Email | Пароль | Роль | Права |
|-------|--------|------|-------|
| admin@example.com | SecurePass123 | Admin (superuser) | Все права |
| manager@example.com | SecurePass123 | Manager | Документы (view, create, update), Задачи (view, create, update) |
| user@example.com | SecurePass123 | User | Документы (view), Задачи (view, create) |
| guest@example.com | SecurePass123 | Guest | Документы (view), Задачи (view) |
| restricted@example.com | SecurePass123 | Guest + ACL deny | **Нет прав** (явный запрет) |

### Матрица прав доступа

| Роль | GET /api/documents/ | POST /api/documents/ | GET /api/tasks/ | POST /api/tasks/ | /api/admin/* |
|------|---------------------|----------------------|-----------------|------------------|--------------|
| Admin | ✅ 200 | ✅ 201 | ✅ 200 | ✅ 201 | ✅ |
| Manager | ✅ 200 | ✅ 201 | ✅ 200 | ✅ 201 | ❌ 403 |
| User | ✅ 200 | ❌ 403 | ✅ 200 | ✅ 201 | ❌ 403 |
| Guest | ✅ 200 | ❌ 403 | ✅ 200 | ❌ 403 | ❌ 403 |
| Restricted | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |

### Алгоритм проверки прав

```
1. Не аутентифицирован → 401 Unauthorized
2. PermissionsOverride (deny) → 403 Forbidden
3. PermissionsOverride (grant) → доступ разрешён
4. RolePermissions → права через роли
5. Superuser → доступ разрешён
6. Не найдено → 403 Forbidden
```

### Команды для тестирования

```bash
# Загрузка тестовых данных
python manage.py loaddata auth_api/fixtures/initial_data.json
python manage.py create_test_users
```

---

## Установка и запуск

1. Создать виртуальное окружение:
   ```bash
   py -m venv .venv
   ```

2. Установить зависимости:
   ```bash
   .venv\Scripts\pip.exe  install -r requirements.txt
   ```

3. Создать `.env` файл на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Применить миграции:
   ```bash
   .venv\Scripts\python.exe manage.py makemigrations
   .venv\Scripts\python.exe manage.py migrate
   ```

5. Загрузить тестовые данные (роли и права):
   ```bash
   .venv\Scripts\python.exe manage.py loaddata auth_api/fixtures/initial_data.json
   ```

6. Создать тестовых пользователей:
   ```bash
   .venv\Scripts\python.exe manage.py create_test_users
   ```

7. Создать суперпользователя (опционально):
   ```bash
   .venv\Scripts\python.exe manage.py createsuperuser
   ```

8. Запустить сервер:
    ```bash
    .venv\Scripts\python.exe manage.py runserver
    ```
---

## Примеры запросов

### Получение токена (вход)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"admin@example.com\", \"password\": \"SecurePass123\"}"
```

Ответ:
```json
{
  "user": {},
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Запрос к защищенному ресурсу

```bash
curl -X GET http://127.0.0.1:8000/api/documents/ ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Тестирование с разными ролями

| Пользователь | Пароль | Что проверить |
|-------------|--------|---------------|
| `admin@example.com` | `SecurePass123` | Полный доступ ко всему |
| `manager@example.com` | `SecurePass123` | Документы/задачи + 403 на admin |
| `user@example.com` | `SecurePass123` | Только просмотр документов |
| `guest@example.com` | `SecurePass123` | Только просмотр |
| `restricted@example.com` | `SecurePass123` | 403 на всё |

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
.venv\Scripts\python.exe manage.py test auth_api.tests
```