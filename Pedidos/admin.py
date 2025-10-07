from django.contrib import admin
from .models import Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'numero_orden', 'solicitante', 'empresa', 'estado_pedido',
        'fecha_creacion', 'fecha_completado', 'estado'
    ]
    list_filter = ['estado_pedido', 'empresa', 'estado', 'fecha_creacion', 'fecha_completado']
    search_fields = [
        'numero_orden', 'solicitante__nombre', 'solicitante__email',
        'empresa__nombre', 'solicitud__id'
    ]
    readonly_fields = [
        'numero_orden', 'solicitud', 'empresa', 'solicitante',
        'fecha_completado', 'fecha_creacion', 'fecha_actualizacion',
        'total', 'cantidad_items'
    ]
    inlines = [DetallePedidoInline]

    fieldsets = (
        ('Información General', {
            'fields': (
                'numero_orden', 'solicitud', 'empresa', 'solicitante',
                'estado_pedido', 'observaciones', 'estado'
            )
        }),
        ('Resumen', {
            'fields': ('total', 'cantidad_items', 'fecha_completado'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['pedido__estado_pedido', 'producto']
    search_fields = ['pedido__numero_orden', 'producto__nombre', 'producto__sku']
    readonly_fields = ['subtotal', 'fecha_creacion', 'fecha_actualizacion']
