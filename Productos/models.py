from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager


class Categoria(BaseModel):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la categoría')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre.title()


class ProductoManager(models.Manager):
    """Manager personalizado para Producto con consultas específicas"""

    def con_stock_bajo(self):
        """Retorna productos activos con stock por debajo del umbral mínimo"""
        return self.filter(estado=True, stock_disponible__lt=models.F('umbral_minimo'))


class Producto(BaseModel):
    nombre = models.CharField(max_length=200, verbose_name='Nombre del producto')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, related_name='productos', null=True, blank=True, verbose_name='Categoría')
    stock_disponible = models.IntegerField(default=0, verbose_name='Stock disponible')
    umbral_minimo = models.IntegerField(default=10, verbose_name='Umbral mínimo de stock')

    objects = ProductoManager()
    activos = ActiveManager()

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.sku} - {self.nombre}".title()

    @property
    def stock_bajo(self):
        """
        Retorna True si el stock disponible está por debajo del umbral mínimo.
        """
        return self.stock_disponible < self.umbral_minimo

    @property
    def stock_reservado(self):
        """
        Calcula el stock reservado sumando las reservas activas.
        """
        from Inventario.models import MovimientoInventario
        reservas = MovimientoInventario.objects.filter(
            producto=self,
            tipo_movimiento='RESERVA',
            estado=True
        ).aggregate(total=models.Sum('cantidad'))['total'] or 0

        liberaciones = MovimientoInventario.objects.filter(
            producto=self,
            tipo_movimiento='LIBERACION_RESERVA',
            estado=True
        ).aggregate(total=models.Sum('cantidad'))['total'] or 0

        return reservas - liberaciones

    @property
    def stock_disponible_real(self):
        """
        Retorna el stock realmente disponible (sin contar reservas).
        """
        return self.stock_disponible - self.stock_reservado

    def tiene_stock_suficiente(self, cantidad):
        """
        Verifica si hay stock suficiente disponible (sin contar reservas).
        """
        return self.stock_disponible_real >= cantidad

    def registrar_entrada(self, cantidad, usuario, observaciones=''):
        """
        Registra una entrada de stock.
        """
        from Inventario.models import MovimientoInventario
        return MovimientoInventario.objects.create(
            tipo_movimiento='ENTRADA',
            producto=self,
            cantidad=cantidad,
            usuario_responsable=usuario,
            observaciones=observaciones
        )

    def registrar_salida(self, cantidad, usuario, observaciones=''):
        """
        Registra una salida de stock.
        """
        from Inventario.models import MovimientoInventario
        if not self.tiene_stock_suficiente(cantidad):
            raise ValidationError(f'Stock insuficiente. Disponible: {self.stock_disponible_real}')

        return MovimientoInventario.objects.create(
            tipo_movimiento='SALIDA',
            producto=self,
            cantidad=cantidad,
            usuario_responsable=usuario,
            observaciones=observaciones
        )

    def reservar_stock(self, cantidad, usuario, pedido, observaciones=''):
        """
        Reserva stock para un pedido.
        """
        from Inventario.models import MovimientoInventario
        if not self.tiene_stock_suficiente(cantidad):
            raise ValidationError(f'Stock insuficiente para reservar. Disponible: {self.stock_disponible_real}')

        return MovimientoInventario.objects.create(
            tipo_movimiento='RESERVA',
            producto=self,
            cantidad=cantidad,
            usuario_responsable=usuario,
            pedido=pedido,
            observaciones=observaciones
        )

    def liberar_reserva(self, cantidad, usuario, pedido, observaciones=''):
        """
        Libera una reserva de stock.
        """
        from Inventario.models import MovimientoInventario
        return MovimientoInventario.objects.create(
            tipo_movimiento='LIBERACION_RESERVA',
            producto=self,
            cantidad=cantidad,
            usuario_responsable=usuario,
            pedido=pedido,
            observaciones=observaciones
        )
