from django.contrib import admin
from .models import Ticket, ComentarioTicket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'categoria', 'prioridad', 'estado', 'usuario', 'fecha_creacion')
    list_filter = ('estado', 'prioridad', 'categoria')
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'clasificacion_automatica', 'confianza_clasificacion')


@admin.register(ComentarioTicket)
class ComentarioTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'usuario', 'fecha', 'es_interno')
    list_filter = ('es_interno',)