from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager
from Pedidos.models import Pedido
from Usuarios.models import Usuario
from .models_notificaciones import NotificacionPago


class PagoManager(models.Manager):
    def pendientes(self):
        return self.filter(estado=True, estado_pago=self.model.Estados.PENDIENTE)

    def completados(self):
        return self.filter(estado=True, estado_pago=self.model.Estados.COMPLETADO)

    def por_pedido(self, pedido):
        return self.filter(estado=True, pedido=pedido)


class Pago(BaseModel):
    class Estados(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PARCIAL = 'PARCIAL', 'Pago Parcial'
        COMPLETADO = 'COMPLETADO', 'Completado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    class MetodosPago(models.TextChoices):
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia Bancaria'
        TARJETA = 'TARJETA', 'Tarjeta de Crédito/Débito'
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        CHEQUE = 'CHEQUE', 'Cheque'
        OTRO = 'OTRO', 'Otro'

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Pedido'
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Monto pagado'
    )
    estado_pago = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
        verbose_name='Estado del pago'
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodosPago.choices,
        verbose_name='Método de pago'
    )
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Referencia/Comprobante'
    )
    fecha_pago = models.DateTimeField(
        verbose_name='Fecha de pago'
    )
    validado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name='pagos_validados',
        null=True,
        blank=True,
        verbose_name='Validado por'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )

    objects = PagoManager()
    activos = ActiveManager()

    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.id} - {self.pedido.numero_orden} - ${self.monto}"

    @property
    def monto_pendiente(self):
        total_pagado = self.pedido.pagos.filter(
            estado=True,
            estado_pago__in=[Pago.Estados.COMPLETADO, Pago.Estados.PARCIAL]
        ).aggregate(models.Sum('monto'))['monto__sum'] or 0

        return max(0, self.pedido.total - total_pagado)
