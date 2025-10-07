from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager
from Empresas.models import Empresa
from Usuarios.models import Usuario
from Productos.models import Producto
from Solicitudes.models import Solicitud


class PedidoManager(models.Manager):
    """Manager personalizado para Pedido con consultas específicas"""

    def pendientes_pago(self):
        return self.filter(estado=True, estado_pedido='PENDIENTE_PAGO')

    def pago_confirmado(self):
        return self.filter(estado=True, estado_pedido='PAGO_CONFIRMADO')

    def en_despacho(self):
        return self.filter(estado=True, estado_pedido='EN_DESPACHO')

    def completados(self):
        return self.filter(estado=True, estado_pedido='COMPLETADO')

    def cancelados(self):
        return self.filter(estado=True, estado_pedido='CANCELADO')


class Pedido(BaseModel):
    ESTADOS_PEDIDO = [
        ('PENDIENTE_PAGO', 'Pendiente de Pago'),
        ('PAGO_CONFIRMADO', 'Pago Confirmado'),
        ('EN_DESPACHO', 'En Despacho'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Solicitud origen'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Empresa'
    )
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='pedidos_realizados',
        verbose_name='Solicitante'
    )
    estado_pedido = models.CharField(
        max_length=30,
        choices=ESTADOS_PEDIDO,
        default='PENDIENTE_PAGO',
        verbose_name='Estado del pedido'
    )
    numero_orden = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Número de orden'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )
    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de completado'
    )

    objects = PedidoManager()
    activos = ActiveManager()

    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido {self.numero_orden} - {self.empresa.nombre} - {self.estado_pedido}"

    @property
    def total(self):
        return sum(detalle.subtotal for detalle in self.detalles.all())

    @property
    def cantidad_items(self):
        return self.detalles.count()

    @property
    def esta_completado(self):
        return self.estado_pedido == 'COMPLETADO'

    @property
    def puede_editarse(self):
        return self.estado_pedido in ['PENDIENTE_PAGO']

    @property
    def puede_cancelarse(self):
        return self.estado_pedido in ['PENDIENTE_PAGO', 'PAGO_CONFIRMADO']


class DetallePedido(BaseModel):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Pedido'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_pedido',
        verbose_name='Producto'
    )
    cantidad = models.IntegerField(
        verbose_name='Cantidad'
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario'
    )

    class Meta:
        db_table = 'detalles_pedido'
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'
        ordering = ['id']
        unique_together = ['pedido', 'producto']

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        if self.precio_unitario < 0:
            raise ValidationError('El precio unitario no puede ser negativo.')

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
