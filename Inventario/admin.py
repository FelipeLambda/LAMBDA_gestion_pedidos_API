from django.contrib import admin
from .models import MovimientoInventario


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tipo_movimiento', 'producto', 'cantidad',
        'usuario_responsable', 'pedido', 'fecha_creacion', 'estado'
    ]
    list_filter = ['tipo_movimiento', 'estado', 'fecha_creacion']
    search_fields = [
        'producto__nombre', 'producto__sku',
        'usuario_responsable__nombre', 'usuario_responsable__email',
        'pedido__numero_orden', 'observaciones'
    ]
    readonly_fields = [
        'tipo_movimiento', 'producto', 'cantidad',
        'usuario_responsable', 'pedido', 'observaciones',
        'fecha_creacion', 'fecha_actualizacion'
    ]

    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('tipo_movimiento', 'producto', 'cantidad', 'observaciones', 'estado')
        }),
        ('Responsable', {
            'fields': ('usuario_responsable', 'pedido'),
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
