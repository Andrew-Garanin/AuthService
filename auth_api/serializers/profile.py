from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'middle_name', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']
    
    def update(self, instance, validated_data):
        """Обновление профиля."""
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.middle_name = validated_data.get('middle_name', instance.middle_name)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    
    def validate(self, data):
        """Проверка нового пароля."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Новые пароли не совпадают'})
        if data['new_password'] == data['old_password']:
            raise serializers.ValidationError({'new_password_confirm': 'Новый пароль не может совпадать со старым'})
        return data
    
    def validate_old_password(self, value):
        """Проверка старого пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value
