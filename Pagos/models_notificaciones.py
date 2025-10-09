from django.db import models
from Base.models import BaseModel
from Pedidos.models import Pedido


class NotificacionPago(BaseModel):
    class TiposNotificacion(models.TextChoices):
        RECORDATORIO_PREVIO = 'RECORDATORIO_PREVIO', 'Recordatorio 3 días antes'
        VENCIMIENTO = 'VENCIMIENTO', 'Notificación de vencimiento'
        MORA_1 = 'MORA_1', 'Primera notificación de mora (15 días)'
        MORA_2 = 'MORA_2', 'Segunda notificación de mora (30 días)'
        MORA_3 = 'MORA_3', 'Tercera notificación de mora (45 días)'
        MORA_4 = 'MORA_4', 'Cuarta notificación de mora (60 días)'
        ACCION_LEGAL = 'ACCION_LEGAL', 'Quinta notificación - Acciones legales'

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='notificaciones_pago',
        verbose_name='Pedido'
    )
    tipo_notificacion = models.CharField(
        max_length=30,
        choices=TiposNotificacion.choices,
        verbose_name='Tipo de notificación'
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de envío'
    )
    email_destinatario = models.EmailField(
        verbose_name='Email destinatario'
    )
    enviado_exitosamente = models.BooleanField(
        default=False,
        verbose_name='Enviado exitosamente'
    )
    error_envio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Error de envío'
    )

    class Meta:
        db_table = 'notificaciones_pago'
        verbose_name = 'Notificación de Pago'
        verbose_name_plural = 'Notificaciones de Pago'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"{self.get_tipo_notificacion_display()} - {self.pedido.numero_orden}"
