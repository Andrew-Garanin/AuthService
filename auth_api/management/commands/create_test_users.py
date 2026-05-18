from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from auth_api.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей с правильными паролями'

    def handle(self, *args, **options):
        password = 'SecurePass123'

        # Удаляем старых тестовых пользователей если есть
        User.objects.filter(email__in=[
            'admin@example.com',
            'manager@example.com',
            'user@example.com',
            'guest@example.com',
            'restricted@example.com'
        ]).delete()

        # Получаем роли
        admin_role = Role.objects.get(name='Admin')
        manager_role = Role.objects.get(name='Manager')
        user_role = Role.objects.get(name='User')
        guest_role = Role.objects.get(name='Guest')

        # Создаём пользователей
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password=password,
            first_name='Admin',
            last_name='User'
        )
        UserRole.objects.create(user=admin, role=admin_role)
        self.stdout.write(self.style.SUCCESS(f'✓ Admin: admin@example.com / {password}'))

        manager = User.objects.create_user(
            email='manager@example.com',
            password=password,
            first_name='Manager',
            last_name='User'
        )
        UserRole.objects.create(user=manager, role=manager_role, assigned_by=admin)
        self.stdout.write(self.style.SUCCESS(f'✓ Manager: manager@example.com / {password}'))

        user = User.objects.create_user(
            email='user@example.com',
            password=password,
            first_name='Regular',
            last_name='User'
        )
        UserRole.objects.create(user=user, role=user_role, assigned_by=admin)
        self.stdout.write(self.style.SUCCESS(f'✓ User: user@example.com / {password}'))

        guest = User.objects.create_user(
            email='guest@example.com',
            password=password,
            first_name='Guest',
            last_name='User'
        )
        UserRole.objects.create(user=guest, role=guest_role, assigned_by=admin)
        self.stdout.write(self.style.SUCCESS(f'✓ Guest: guest@example.com / {password}'))

        restricted = User.objects.create_user(
            email='restricted@example.com',
            password=password,
            first_name='Restricted',
            last_name='User'
        )
        UserRole.objects.create(user=restricted, role=guest_role, assigned_by=admin)
        self.stdout.write(self.style.SUCCESS(f'✓ Restricted: restricted@example.com / {password}'))

        self.stdout.write(self.style.SUCCESS('\nВсе тестовые пользователи созданы!'))
