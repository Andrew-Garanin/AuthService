from rest_framework import serializers
from ..models import Role, Permission, UserRole, PermissionsOverride


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для ролей (админка)."""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class PermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для прав (админка)."""
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'resource', 'action', 'description']


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для назначения ролей пользователям (админка)."""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'assigned_at', 'assigned_by']
        read_only_fields = ['assigned_at', 'assigned_by']


class PermissionsOverrideSerializer(serializers.ModelSerializer):
    """Сериализатор для переопределения прав (админка)."""
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = PermissionsOverride
        fields = ['id', 'user', 'user_email', 'resource_type', 'resource_id', 
                  'permission', 'permission_codename', 'action_type', 'description', 
                  'granted_by', 'created_at', 'expires_at']
        read_only_fields = ['created_at', 'granted_by']
