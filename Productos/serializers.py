from rest_framework import serializers
from .models import Categoria, Producto

class CategoriaSerializer(serializers.ModelSerializer):
    total_productos = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'estado', 'total_productos', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def get_total_productos(self, obj):
        return obj.productos.filter(estado=True).count()


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    stock_reservado = serializers.IntegerField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'sku', 'precio', 'categoria', 'categoria_nombre',
            'stock_disponible', 'umbral_minimo', 'stock_bajo', 'stock_reservado',
            'estado', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'stock_bajo', 'stock_reservado']


class ProductoListSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'sku', 'nombre', 'precio', 'categoria_nombre', 'stock_disponible', 'stock_bajo', 'estado']


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar productos.
    """
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'sku', 'precio', 'categoria', 'stock_disponible', 'umbral_minimo', 'estado']

    def validate_sku(self, value):
        queryset = Producto.objects.filter(sku=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Ya existe un producto con este SKU.")
        return value

    def validate_precio(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a cero.")
        return value

    def validate_umbral_minimo(self, value):
        if value < 0:
            raise serializers.ValidationError("El umbral mínimo no puede ser negativo.")
        return value
