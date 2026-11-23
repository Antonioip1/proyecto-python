from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Usuario personalizado con roles del sistema"""
    ROLES = (
        ('admin', 'Administrador'),
        ('tecnico', 'Técnico de Soporte'),
        ('usuario', 'Usuario Final'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default='usuario',
        verbose_name='Rol'
    )
    telefono = models.CharField(max_length=15, blank=True, verbose_name='Teléfono')
    departamento = models.CharField(max_length=100, blank=True, verbose_name='Departamento')
    debe_cambiar_password = models.BooleanField(
        default=False,
        verbose_name='Debe cambiar contraseña'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"