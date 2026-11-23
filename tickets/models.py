from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone


class Ticket(models.Model):
    """Solicitudes de soporte técnico"""
    PRIORIDADES = (
        ('critica', 'CRÍTICA'),
        ('alta', 'ALTA'),
        ('media', 'MEDIA'),
        ('baja', 'BAJA'),
    )

    CATEGORIAS = (
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('red', 'Red/Conectividad'),
        ('correo', 'Correo Electrónico'),
        ('sistema', 'Sistema Operativo'),
        ('periferico', 'Periférico'),
        ('otro', 'Otro'),
    )

    ESTADOS = (
        ('abierto', 'Abierto'),
        ('asignado', 'Asignado'),
        ('en_progreso', 'En Progreso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
        ('rechazado', 'Rechazado'),
    )

    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIAS, default='otro', verbose_name='Categoría'
    )
    prioridad = models.CharField(
        max_length=20, choices=PRIORIDADES, default='media', verbose_name='Prioridad'
    )
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='abierto', verbose_name='Estado'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets_creados',
        verbose_name='Usuario Creador'
    )
    tecnico_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets_asignados',
        verbose_name='Técnico Asignado'
    )
    activo_relacionado = models.ForeignKey(
        'assets.ActivoTecnologico',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Activo Relacionado'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_asignacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Asignación')
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Resolución')

    clasificacion_automatica = models.CharField(
        max_length=50, blank=True, verbose_name='Clasificación Automática'
    )
    confianza_clasificacion = models.FloatField(
        default=0.0, verbose_name='Confianza de Clasificación'
    )

    tiempo_respuesta_minutos = models.IntegerField(
        null=True, blank=True, verbose_name='Tiempo de Respuesta (min)'
    )
    satisfaccion_usuario = models.IntegerField(
        null=True, blank=True, verbose_name='Satisfacción (1-5)'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.id} - {self.titulo[:50]}"

    @property
    def tiempo_transcurrido_horas(self):
        delta = timezone.now() - self.fecha_creacion
        return round(delta.total_seconds() / 3600, 1)


class ComentarioTicket(models.Model):
    """Comentarios dentro de un ticket"""
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='comentarios'
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField(verbose_name='Texto')
    fecha = models.DateTimeField(auto_now_add=True)
    es_interno = models.BooleanField(default=False, verbose_name='Es Interno')

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['fecha']

    def __str__(self):
        return f"Comentario en #{self.ticket.id} por {self.usuario.username}"