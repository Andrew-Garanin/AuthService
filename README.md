# Система аутентификации и авторизации

## Описание архитектуры

Приложение реализует собственную систему управления доступом на основе гибридной модели **RBAC (Role-Based Access Control)** + **ACL (Access Control List)**.

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
| `name` | Char(100) | Название роли (уникальное) |
| `description` | Text | Описание роли |
| `created_at` | DateTime | Дата создания |

**Стандартные роли:**
- `Admin` — полный доступ ко всем ресурсам
- `Manager` — управление контентом (документы, задачи)
- `User` — базовые права (просмотр, создание своих ресурсов)
- `Guest` — только просмотр

### 3. Модель `Permission`
Атомарное право доступа.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `name` | Char(200) | Человеко-читаемое название |
| `codename` | Char(100) | Уникальный код (например, `documents_view`) |
| `resource` | Char(100) | Тип ресурса (`documents`, `tasks`, `users`, `acl`) |
| `action` | Char(50) | Действие (`view`, `create`, `update`, `delete`, `manage`) |
| `description` | Text | Описание |
| `created_at` | DateTime | Дата создания |

**Примеры прав:**
- `documents_view` — просмотр документов
- `documents_create` — создание документов
- `documents_update` — редактирование документов
- `documents_delete` — удаление документов
- `tasks_view`, `tasks_create`, `tasks_update`, `tasks_delete`
- `users_view`, `users_manage`
- `acl_manage` — управление переопределениями прав

### 4. Модель `UserRole`
Связь пользователя с ролью (многие-ко-многим).

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `user` | FK → User | Пользователь |
| `role` | FK → Role | Роль |
| `assigned_at` | DateTime | Дата назначения |
| `assigned_by` | FK → User | Кто назначил |

**Уникальность:** один пользователь может иметь одну и ту же роль только один раз.

### 5. Модель `RolePermission`
Связь роли с правами (многие-ко-многим).

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Первичный ключ |
| `role` | FK → Role | Роль |
| `permission` | FK → Permission | Право |
| `granted_at` | DateTime | Дата выдачи |

**Уникальность:** одна роль может иметь одно право только один раз.

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

**Примеры использования:**
- Запретить конкретному пользователю удалять документы (`action_type=deny`)
- Дать временный доступ к задаче другому пользователю (`expires_at`)
- Разрешить всем пользователям (user=null) просматривать публичный документ

---

## Приоритет проверки прав

При запросе к ресурсу система проверяет права в следующем порядке:

1. **PermissionsOverride (deny)** — если есть явный запрет для пользователя → **403 Forbidden**
2. **PermissionsOverride (grant)** — если есть явное разрешение → **доступ разрешён**
3. **RolePermissions** — права через роли пользователя
4. **Superuser** — если `is_superuser=True` → **доступ разрешён**
5. Если право не найдено → **403 Forbidden**
6. Если пользователь не аутентифицирован → **401 Unauthorized**

---

## API Endpoints (планируемые)

### Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| GET | `/api/auth/profile/` | Профиль текущего пользователя |
| PUT | `/api/auth/profile/` | Обновление профиля |
| DELETE | `/api/auth/profile/` | Мягкое удаление аккаунта |

### Управление правами (Admin-only)
| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/api/admin/roles/` | CRUD ролей |
| GET | `/api/admin/permissions/` | Список прав |
| GET/POST | `/api/admin/users/<id>/roles/` | Назначение ролей пользователю |
| GET/POST/DELETE | `/api/admin/acl/` | Управление переопределениями прав |

### Mock-ресурсы
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/documents/` | Список документов |
| GET/POST | `/api/documents/<id>/` | Документ / создание |
| PUT/DELETE | `/api/documents/<id>/` | Обновление / удаление |
| GET | `/api/tasks/` | Список задач |
| ... | ... | ... |

---

## Установка и запуск

1. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Создать `.env` файл на основе `.env.example`

3. Применить миграции:
   ```bash
   python manage.py migrate
   ```

4. Загрузить тестовые данные:
   ```bash
   python manage.py loaddata auth_api/fixtures/initial_data.json
   ```

5. Создать суперпользователя:
   ```bash
   python manage.py createsuperuser
   ```

6. Запустить сервер:
   ```bash
   python manage.py runserver
   ```

---

## Тестовые данные

После загрузки `initial_data.json` в базе будут:

### Роли
- Admin
- Manager
- User
- Guest

### Права
- documents_view, documents_create, documents_update, documents_delete
- tasks_view, tasks_create, tasks_update, tasks_delete
- users_view, users_manage
- acl_manage

### Назначения прав ролям
- **Admin**: все права
- **Manager**: документы (view, create, update), задачи (view, create, update)
- **User**: документы (view), задачи (view, create)
- **Guest**: документы (view), задачи (view)