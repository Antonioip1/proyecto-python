from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone


class CategoriaActivo(models.Model):
    """Categorías de activos tecnológicos"""
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Categoría de Activo'
        verbose_name_plural = 'Categorías de Activos'

    def __str__(self):
        return self.nombre


class ActivoTecnologico(models.Model):
    """Equipos informáticos de la institución"""
    ESTADOS = (
        ('operativo', 'Operativo'),
        ('mantenimiento', 'En Mantenimiento'),
        ('reparacion', 'En Reparación'),
        ('obsoleto', 'Obsoleto'),
        ('baja', 'Dado de Baja'),
    )

    codigo_inventario = models.CharField(
        max_length=50, unique=True, verbose_name='Código de Inventario'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    categoria = models.ForeignKey(
        CategoriaActivo, on_delete=models.PROTECT, verbose_name='Categoría'
    )
    modelo = models.CharField(max_length=100, verbose_name='Modelo')
    serie = models.CharField(max_length=100, blank=True, verbose_name='Serie')

    procesador = models.CharField(max_length=100, blank=True, verbose_name='Procesador')
    ram = models.CharField(max_length=50, blank=True, verbose_name='RAM')
    disco = models.CharField(max_length=50, blank=True, verbose_name='Disco')

    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='operativo', verbose_name='Estado'
    )
    ubicacion = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    usuario_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activos_asignados',
        verbose_name='Usuario Asignado'
    )

    fecha_adquisicion = models.DateField(verbose_name='Fecha de Adquisición')
    fecha_ultimo_mantenimiento = models.DateField(
        null=True, blank=True, verbose_name='Último Mantenimiento'
    )
    garantia_hasta = models.DateField(
        null=True, blank=True, verbose_name='Garantía Hasta'
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activo Tecnológico'
        verbose_name_plural = 'Activos Tecnológicos'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.codigo_inventario} - {self.nombre}"

    @property
    def esta_en_garantia(self):
        if self.garantia_hasta:
            return self.garantia_hasta >= timezone.now().date()
        return False