from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager
from Productos.models import Producto
from Usuarios.models import Usuario


class MovimientoInventarioManager(models.Manager):
    """Manager personalizado para MovimientoInventario con consultas específicas"""

    def entradas(self):
        return self.filter(estado=True, tipo_movimiento='ENTRADA')

    def salidas(self):
        return self.filter(estado=True, tipo_movimiento='SALIDA')

    def reservas_activas(self):
        return self.filter(estado=True, tipo_movimiento='RESERVA')

    def por_producto(self, producto):
        return self.filter(estado=True, producto=producto)


class MovimientoInventario(BaseModel):
    TIPOS_MOVIMIENTO = [
        ('ENTRADA', 'Entrada de Stock'),
        ('SALIDA', 'Salida de Stock'),
        ('RESERVA', 'Reserva de Stock'),
        ('LIBERACION_RESERVA', 'Liberación de Reserva'),
    ]

    tipo_movimiento = models.CharField(
        max_length=30,
        choices=TIPOS_MOVIMIENTO,
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

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')

        if self.tipo_movimiento in ['RESERVA', 'LIBERACION_RESERVA'] and not self.pedido:
            raise ValidationError('Las reservas y liberaciones deben tener un pedido asociado.')

        if self.tipo_movimiento in ['SALIDA', 'RESERVA']:
            if not self.pk: 
                stock_disponible = self.producto.stock_disponible - self.producto.stock_reservado
                if self.cantidad > stock_disponible:
                    raise ValidationError(
                        f'Stock insuficiente. Disponible: {stock_disponible}, Solicitado: {self.cantidad}'
                    )

    @property
    def afecta_stock_disponible(self):
        return self.tipo_movimiento in ['ENTRADA', 'SALIDA']

    @property
    def afecta_stock_reservado(self):
        return self.tipo_movimiento in ['RESERVA', 'LIBERACION_RESERVA']

    @property
    def es_incremento(self):
        return self.tipo_movimiento in ['ENTRADA', 'LIBERACION_RESERVA']

    @property
    def es_decremento(self):
        return self.tipo_movimiento in ['SALIDA', 'RESERVA']

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.pk:  
            if self.tipo_movimiento == 'ENTRADA':
                self.producto.stock_disponible += self.cantidad
            elif self.tipo_movimiento == 'SALIDA':
                self.producto.stock_disponible -= self.cantidad

            self.producto.save()

        super().save(*args, **kwargs)
