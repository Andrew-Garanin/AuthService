from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    """
    Кастомный менеджер для модели User.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email должен быть указан')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    async def acreate_user(self, email, password=None, **extra_fields):
        """Асинхронная версия create_user."""
        if not email:
            raise ValueError('Email должен быть указан')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        await user.asave(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

    async def acreate_superuser(self, email, password=None, **extra_fields):
        """Асинхронная версия create_superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return await self.acreate_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    """
    Кастомная модель пользователя с email для аутентификации.
    Без поля username. Первичный ключ — UUID.
    Права управления через кастомные модели: Role, Permission, UserRole, RolePermission.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Имя", max_length=150, blank=False)
    last_name = models.CharField("Фамилия", max_length=150, blank=False)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Доступ в админку", default=False)
    is_superuser = models.BooleanField("Суперпользователь", default=False)

    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return f"{full_name} ({self.email})"

    def has_perm(self, perm, obj=None):
        """
        Проверяет, есть ли у пользователя конкретное право.
        Для простоты — суперпользователь имеет все права.
        """
        return self.is_active and (self.is_superuser or self._has_perm(perm))

    def has_module_perms(self, app_label):
        """
        Проверяет, есть ли у пользователя права на модуль (для админки).
        Суперпользователь и staff имеют доступ.
        """
        return self.is_active and (self.is_superuser or self.is_staff)

    def _has_perm(self, perm):
        """
        Внутренняя проверка права через роли и переопределения.
        """
        # TODO: реализовать проверку через UserRole, RolePermission, PermissionsOverride
        return False

    def soft_delete(self):
        """
        Мягкое удаление пользователя — устанавливает is_active=False.
        """
        self.is_active = False
        self.save()
    
    async def soft_delete_async(self):
        """
        Асинхронное мягкое удаление пользователя — устанавливает is_active=False.
        """
        self.is_active = False
        await self.asave()

class Role(models.Model):
    """
    Роль пользователя.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Название", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
    
    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Атомарное право доступа к ресурсу.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Название", max_length=200, unique=True)
    codename = models.CharField("Кодовое имя", max_length=100, unique=True)
    resource = models.CharField("Ресурс", max_length=100, help_text="Тип ресурса (documents, tasks, users и т.д.)")
    action = models.CharField("Действие", max_length=50, help_text="Действие (view, create, update, delete)")
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    
    class Meta:
        verbose_name = "Право"
        verbose_name_plural = "Права"
        ordering = ['resource', 'action']
    
    def __str__(self):
        return f"{self.codename} ({self.resource}.{self.action})"


class UserRole(models.Model):
    """
    Связь пользователя с ролью.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name="Пользователь"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_users',
        verbose_name="Роль"
    )
    assigned_at = models.DateTimeField("Дата назначения", auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name="Назначил"
    )
    
    class Meta:
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user} - {self.role}"


class RolePermission(models.Model):
    """
    Связь роли с правами.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name="Роль"
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='permission_roles',
        verbose_name="Право"
    )
    granted_at = models.DateTimeField("Дата выдачи", auto_now_add=True)
    
    class Meta:
        verbose_name = "Право роли"
        verbose_name_plural = "Права ролей"
        unique_together = ['role', 'permission']
    
    def __str__(self):
        return f"{self.role} - {self.permission}"


class PermissionsOverride(models.Model):
    """
    Явное переопределение прав для конкретного пользователя на ресурс.
    Позволяет давать или отзывать права индивидуально, игнорируя роли.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    
    RESOURCE_TYPES = [
        ('documents', 'Документы'),
        ('tasks', 'Задачи'),
        ('users', 'Пользователи'),
        ('custom', 'Свой ресурс'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permission_overrides',
        verbose_name="Пользователь",
        null=True,
        blank=True,
        help_text="Если null — применяется ко всем пользователям"
    )
    resource_type = models.CharField("Тип ресурса", max_length=50, choices=RESOURCE_TYPES)
    resource_id = models.CharField("ID ресурса", max_length=100, blank=True, help_text="ID конкретного ресурса (пусто — для всех ресурсов типа)")
    
    ACTION_TYPES = [
        ('grant', 'Разрешить'),
        ('deny', 'Запретить'),
    ]
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='permission_overrides',
        verbose_name="Право"
    )
    action_type = models.CharField("Тип действия", max_length=10, choices=ACTION_TYPES, default='grant')
    description = models.TextField("Описание", blank=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_overrides',
        verbose_name="Выдал"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает", null=True, blank=True)
    
    class Meta:
        verbose_name = "Переопределение прав"
        verbose_name_plural = "Переопределения прав"
        ordering = ['-created_at']
    
    def __str__(self):
        action = "Разрешить" if self.action_type == 'grant' else "Запретить"
        user_str = self.user.email if self.user else "Все пользователи"
        return f"{action}: {self.permission} для {user_str} на {self.resource_type}"

