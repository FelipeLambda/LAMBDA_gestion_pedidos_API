from django.db import models
from Base.models import BaseModel

class Categoria(BaseModel):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la categoría')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
        permissions = (
            ('ver_categorias', 'Puede ver categorías'),
            ('crear_categoria', 'Puede crear categorías'),
            ('editar_categoria', 'Puede editar categorías'),
        )

    def __str__(self):
        return f"{self.nombre}".title()


class Producto(BaseModel):
    nombre = models.CharField(max_length=200, verbose_name='Nombre del producto')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, related_name='productos', null=True, blank=True, verbose_name='Categoría')
    stock_disponible = models.IntegerField(default=0, verbose_name='Stock disponible')
    umbral_minimo = models.IntegerField(default=10, verbose_name='Umbral mínimo de stock')

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        permissions = (
            ('ver_productos', 'Puede ver productos'),
            ('crear_producto', 'Puede crear productos'),
            ('editar_producto', 'Puede editar productos'),
            ('gestionar_catalogo', 'Puede gestionar el catálogo completo'),
            ('ver_alertas_stock', 'Puede ver alertas de stock bajo'),
        )

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
        Se implementará cuando exista el modelo ReservaStock.
        """
        # Se implementara cuando exista Stock
        return 0
