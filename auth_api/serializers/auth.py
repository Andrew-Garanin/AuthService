from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'middle_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        """Проверка совпадения паролей."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return data
    
    def create(self, validated_data):
        """Создание пользователя без password_confirm."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            middle_name=validated_data.get('middle_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """Проверка логина и пароля."""
        from django.contrib.auth import authenticate
        
        user = authenticate(
            request=self.context.get('request'),
            email=data['email'],
            password=data['password']
        )
        
        if not user:
            raise serializers.ValidationError('Неверный email или пароль')
        
        if not user.is_active:
            raise serializers.ValidationError('Аккаунт деактивирован')
        
        data['user'] = user
        return data


class LogoutSerializer(serializers.Serializer):
    """Сериализатор для выхода пользователя."""
    refresh_token = serializers.CharField(required=True)
