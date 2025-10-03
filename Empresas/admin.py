from django.contrib import admin
from .models import Empresa, Area


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'sector', 'pagar_despues', 'estado', 'fecha_creacion']
    list_filter = ['pagar_despues', 'estado', 'sector']
    search_fields = ['nombre', 'nit', 'correo_contacto']
    ordering = ['nombre']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'empresa']
    search_fields = ['nombre', 'empresa__nombre']
    ordering = ['empresa', 'nombre']
