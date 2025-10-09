from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from Base.models import BaseModel, ActiveManager
from Empresas.models import Empresa
from Usuarios.models import Usuario
from Productos.models import Producto
from Solicitudes.models import Solicitud


class PedidoManager(models.Manager):
    def pendientes_pago(self):
        from Pedidos.models import Pedido
        return self.filter(estado=True, estado_pedido=Pedido.Estados.PENDIENTE_PAGO)

    def pago_confirmado(self):
        from Pedidos.models import Pedido
        return self.filter(estado=True, estado_pedido=Pedido.Estados.PAGO_CONFIRMADO)

    def en_despacho(self):
        from Pedidos.models import Pedido
        return self.filter(estado=True, estado_pedido=Pedido.Estados.EN_DESPACHO)

    def completados(self):
        from Pedidos.models import Pedido
        return self.filter(estado=True, estado_pedido=Pedido.Estados.COMPLETADO)

    def cancelados(self):
        from Pedidos.models import Pedido
        return self.filter(estado=True, estado_pedido=Pedido.Estados.CANCELADO)


class Pedido(BaseModel):
    class Estados(models.TextChoices):
        PENDIENTE_PAGO = 'PENDIENTE_PAGO', 'Pendiente de Pago'
        PAGO_CONFIRMADO = 'PAGO_CONFIRMADO', 'Pago Confirmado'
        EN_DESPACHO = 'EN_DESPACHO', 'En Despacho'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    class TiposPago(models.TextChoices):
        INMEDIATO = 'INMEDIATO', 'Pago Inmediato'
        DIFERIDO = 'DIFERIDO', 'Pago Diferido'

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
        choices=Estados.choices,
        default=Estados.PENDIENTE_PAGO,
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

    tipo_pago = models.CharField(
        max_length=20,
        choices=TiposPago.choices,
        default=TiposPago.INMEDIATO,
        verbose_name='Tipo de pago'
    )
    fecha_limite_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha límite de pago'
    )
    pago_diferido_aprobado = models.BooleanField(
        default=False,
        verbose_name='Pago diferido aprobado'
    )
    aprobador_pago_diferido = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_diferidos_aprobados',
        verbose_name='Aprobador pago diferido'
    )
    fecha_aprobacion_pago_diferido = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación pago diferido'
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
        return self.estado_pedido == Pedido.Estados.COMPLETADO

    @property
    def puede_editarse(self):
        return self.estado_pedido in [Pedido.Estados.PENDIENTE_PAGO]

    @property
    def puede_cancelarse(self):
        return self.estado_pedido in [Pedido.Estados.PENDIENTE_PAGO, Pedido.Estados.PAGO_CONFIRMADO]

    @property
    def dias_para_vencimiento(self):
        if self.tipo_pago == Pedido.TiposPago.DIFERIDO and self.fecha_limite_pago:
            dias = (self.fecha_limite_pago - timezone.now()).days
            return dias
        return None

    @property
    def pago_vencido(self):
        if self.tipo_pago == Pedido.TiposPago.DIFERIDO and self.fecha_limite_pago:
            return timezone.now() > self.fecha_limite_pago
        return False


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

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
