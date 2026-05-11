from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, UserRole, RolePermission, PermissionsOverride


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'resource', 'action', 'created_at']
    list_filter = ['resource', 'action']
    search_fields = ['name', 'codename', 'resource']
    ordering = ['resource', 'action']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__email', 'role__name']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'granted_at']
    list_filter = ['role', 'permission__resource', 'permission__action']
    search_fields = ['role__name', 'permission__codename']


@admin.register(PermissionsOverride)
class PermissionsOverrideAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource_type', 'resource_id', 'permission', 'action_type', 'created_at', 'expires_at']
    list_filter = ['resource_type', 'action_type', 'expires_at']
    search_fields = ['user__email', 'resource_id', 'permission__codename']
    readonly_fields = ['created_at', 'id']


class UserAdmin(BaseUserAdmin):
    """
    Кастомная админка для модели User.
    """
    list_display = ('email', 'first_name', 'last_name', 'middle_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'middle_name')
    
    # Поля, которые нельзя редактировать
    readonly_fields = ('date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'middle_name')}),
        ('Статус', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Важные даты', {'fields': ('date_joined',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_superuser'),
        }),
    )

    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
