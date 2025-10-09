from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager
from Productos.models import Producto
from Usuarios.models import Usuario


class MovimientoInventarioManager(models.Manager):
    def entradas(self):
        from Inventario.models import MovimientoInventario
        return self.filter(estado=True, tipo_movimiento=MovimientoInventario.TiposMovimiento.ENTRADA)

    def salidas(self):
        from Inventario.models import MovimientoInventario
        return self.filter(estado=True, tipo_movimiento=MovimientoInventario.TiposMovimiento.SALIDA)

    def reservas_activas(self):
        from Inventario.models import MovimientoInventario
        return self.filter(estado=True, tipo_movimiento=MovimientoInventario.TiposMovimiento.RESERVA)

    def por_producto(self, producto):
        return self.filter(estado=True, producto=producto)


class MovimientoInventario(BaseModel):
    class TiposMovimiento(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada de Stock'
        SALIDA = 'SALIDA', 'Salida de Stock'
        RESERVA = 'RESERVA', 'Reserva de Stock'
        LIBERACION_RESERVA = 'LIBERACION_RESERVA', 'Liberación de Reserva'

    tipo_movimiento = models.CharField(
        max_length=30,
        choices=TiposMovimiento.choices,
        verbose_name='Tipo de movimiento'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Producto'
    )
    cantidad = models.IntegerField(
        verbose_name='Cantidad'
    )
    usuario_responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='movimientos_inventario',
        verbose_name='Usuario responsable'
    )
    pedido = models.ForeignKey(
        'Pedidos.Pedido',
        on_delete=models.SET_NULL,
        related_name='movimientos_inventario',
        null=True,
        blank=True,
        verbose_name='Pedido relacionado'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )

    objects = MovimientoInventarioManager()
    activos = ActiveManager()

    class Meta:
        db_table = 'movimientos_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.producto.nombre} x{self.cantidad}"

    @property
    def afecta_stock_disponible(self):
        T = MovimientoInventario.TiposMovimiento
        return self.tipo_movimiento in [T.ENTRADA, T.SALIDA]

    @property
    def afecta_stock_reservado(self):
        T = MovimientoInventario.TiposMovimiento
        return self.tipo_movimiento in [T.RESERVA, T.LIBERACION_RESERVA]

    @property
    def es_incremento(self):
        T = MovimientoInventario.TiposMovimiento
        return self.tipo_movimiento in [T.ENTRADA, T.LIBERACION_RESERVA]

    @property
    def es_decremento(self):
        T = MovimientoInventario.TiposMovimiento
        return self.tipo_movimiento in [T.SALIDA, T.RESERVA]
