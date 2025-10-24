from django.contrib import admin
from .models import Pago
from .models_notificaciones import NotificacionPago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'monto', 'estado_pago', 'metodo_pago', 'fecha_pago']
    list_filter = ['estado_pago', 'metodo_pago', 'fecha_pago']
    search_fields = ['pedido__numero_orden', 'referencia_pago']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(NotificacionPago)
class NotificacionPagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'tipo_notificacion', 'email_destinatario', 'enviado_exitosamente', 'fecha_envio']
    list_filter = ['tipo_notificacion', 'enviado_exitosamente', 'fecha_envio']
    search_fields = ['pedido__numero_orden', 'email_destinatario']
    readonly_fields = ['fecha_envio', 'fecha_creacion', 'fecha_actualizacion']
