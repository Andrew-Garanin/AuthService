from rest_framework import serializers


class DocumentSerializer(serializers.Serializer):
    """Mock-сериализатор для документов."""
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.EmailField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_public = serializers.BooleanField(default=False)
    
    def create(self, validated_data):
        """Mock-создание (не сохраняет в БД)."""
        return validated_data
    
    def update(self, instance, validated_data):
        """Mock-обновление."""
        for attr, value in validated_data.items():
            instance[attr] = value
        return instance


class TaskSerializer(serializers.Serializer):
    """Mock-сериализатор для задач."""
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], default='pending')
    priority = serializers.ChoiceField(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    assignee = serializers.EmailField(required=False, allow_blank=True)
    owner = serializers.EmailField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        """Mock-создание."""
        return validated_data
    
    def update(self, instance, validated_data):
        """Mock-обновление."""
        for attr, value in validated_data.items():
            instance[attr] = value
        return instance