from rest_framework import serializers
from .models import MovimientoInventario
from Productos.models import Producto


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario_responsable.nombre', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero_orden', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'tipo_movimiento', 'tipo_movimiento_display',
            'producto', 'producto_nombre', 'producto_sku',
            'cantidad', 'usuario_responsable', 'usuario_nombre',
            'pedido', 'pedido_numero', 'observaciones',
            'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_actualizacion'
        ]


class RegistrarMovimientoSerializer(serializers.Serializer):
    tipo_movimiento = serializers.ChoiceField(
        choices=['ENTRADA', 'SALIDA'],
        required=True
    )
    producto_id = serializers.IntegerField(required=True)
    cantidad = serializers.IntegerField(required=True, min_value=1)
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate_producto_id(self, value):
        try:
            producto = Producto.objects.get(pk=value, estado=True)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado o inactivo.")
        return value

    def validate(self, attrs):
        tipo = attrs.get('tipo_movimiento')
        producto_id = attrs.get('producto_id')
        cantidad = attrs.get('cantidad')

        if tipo == 'SALIDA':
            try:
                producto = Producto.objects.get(pk=producto_id)
                if not producto.tiene_stock_suficiente(cantidad):
                    raise serializers.ValidationError({
                        "cantidad": f"Stock insuficiente. Disponible: {producto.stock_disponible_real}, Solicitado: {cantidad}"
                    })
            except Producto.DoesNotExist:
                pass

        return attrs


class StockProductoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(source='id', read_only=True)
    producto_nombre = serializers.CharField(source='nombre', read_only=True)
    producto_sku = serializers.CharField(source='sku', read_only=True)
    stock_disponible = serializers.IntegerField(read_only=True)
    stock_reservado = serializers.IntegerField(read_only=True)
    stock_disponible_real = serializers.IntegerField(read_only=True)
    umbral_minimo = serializers.IntegerField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
