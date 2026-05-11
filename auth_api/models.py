from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
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


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя с email для аутентификации.
    Без поля username. Первичный ключ — UUID.
    """
    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Имя", max_length=150, blank=False)
    last_name = models.CharField("Фамилия", max_length=150, blank=False)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Доступ в админку", default=False)
    
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)
    
    # Явно переопределяем поля из PermissionsMixin с уникальным related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        related_name='auth_api_users',
        help_text='Группы, к которым принадлежит пользователь.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права доступа',
        blank=True,
        related_name='auth_api_users',
        help_text='Список прав доступа пользователя.'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    
    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return f"{full_name} ({self.email})"

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

    async def soft_delete_async(self):
        """
        Мягкое удаление пользователя — устанавливает is_active=False.
        """
        self.is_active = False
        await self.asave()
