from django.contrib import admin
from .models import Solicitud, DetalleSolicitud

class DetalleSolicitudInline(admin.TabularInline):
    model = DetalleSolicitud
    extra = 1
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'solicitante', 'empresa', 'area', 'estado_solicitud',
        'fecha_creacion', 'estado'
    ]
    list_filter = ['estado_solicitud', 'empresa', 'estado', 'fecha_creacion']
    search_fields = ['solicitante__nombre', 'solicitante__email', 'empresa__nombre']
    readonly_fields = [
        'fecha_creacion', 'fecha_actualizacion',
        'validador_financiero', 'fecha_validacion_financiero',
        'validador_abastecimiento', 'fecha_validacion_abastecimiento'
    ]
    inlines = [DetalleSolicitudInline]

    fieldsets = (
        ('Información General', {
            'fields': ('empresa', 'area', 'solicitante', 'estado_solicitud', 'observaciones', 'estado')
        }),
        ('Validación Financiera', {
            'fields': ('validador_financiero', 'fecha_validacion_financiero', 'observaciones_financiero'),
            'classes': ('collapse',)
        }),
        ('Validación Abastecimiento', {
            'fields': ('validador_abastecimiento', 'fecha_validacion_abastecimiento', 'observaciones_abastecimiento'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetalleSolicitud)
class DetalleSolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitud', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['solicitud__estado_solicitud', 'producto']
    search_fields = ['solicitud__id', 'producto__nombre', 'producto__sku']
    readonly_fields = ['subtotal', 'fecha_creacion', 'fecha_actualizacion']
