from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea el administrador maestro del sistema'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='123456')
        parser.add_argument('--email', default='admin@fundacion.gob.ve')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.role = 'admin'
            user.debe_cambiar_password = True
            user.save()
            self.stdout.write(self.style.WARNING(
                f'[OK] Usuario "{username}" ya existia. Contrasena actualizada.'
            ))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin',
                first_name='Administrador',
                last_name='Maestro',
                debe_cambiar_password=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Administrador maestro creado: {username}'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n=== CREDENCIALES DE ACCESO ===\n'
            f'   Usuario: {username}\n'
            f'   Contrasena: {password}\n'
            f'   (Debe cambiar contrasena al primer inicio de sesion)\n'
        ))