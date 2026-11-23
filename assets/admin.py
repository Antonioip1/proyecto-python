from django.contrib import admin
from .models import CategoriaActivo, ActivoTecnologico


@admin.register(CategoriaActivo)
class CategoriaActivoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(ActivoTecnologico)
class ActivoTecnologicoAdmin(admin.ModelAdmin):
    list_display = ('codigo_inventario', 'nombre', 'categoria', 'estado', 'ubicacion')
    list_filter = ('estado', 'categoria')
    search_fields = ('codigo_inventario', 'nombre', 'modelo', 'serie')
    readonly_fields = ('fecha_registro',)