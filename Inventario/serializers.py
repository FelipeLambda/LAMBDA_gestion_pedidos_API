from rest_framework import serializers
from .models import MovimientoInventario
from Productos.models import Producto
from Productos.serializers import ProductoListSerializer


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoListSerializer(source='producto', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario_responsable.nombre', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero_orden', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'tipo_movimiento', 'tipo_movimiento_display',
            'producto', 'producto_detalle',
            'cantidad', 'usuario_responsable', 'usuario_nombre',
            'pedido', 'pedido_numero', 'observaciones',
            'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_actualizacion'
        ]


class RegistrarMovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoInventario
        fields = ['tipo_movimiento', 'producto', 'cantidad', 'observaciones']
        extra_kwargs = {
            'tipo_movimiento': {
                'required': True
            },
            'producto': {
                'required': True
            },
            'cantidad': {
                'required': True,
                'min_value': 1
            },
            'observaciones': {
                'required': False,
                'allow_blank': True
            }
        }

    def validate_tipo_movimiento(self, value):
        if value not in [MovimientoInventario.TiposMovimiento.ENTRADA, MovimientoInventario.TiposMovimiento.SALIDA]:
            raise serializers.ValidationError("Solo se permiten movimientos de tipo ENTRADA o SALIDA.")
        return value

    def validate_producto(self, value):
        if not value.estado:
            raise serializers.ValidationError("El producto está inactivo.")
        return value

    def validate(self, attrs):
        tipo = attrs.get('tipo_movimiento')
        producto = attrs.get('producto')
        cantidad = attrs.get('cantidad')

        if tipo == MovimientoInventario.TiposMovimiento.SALIDA:
            if not producto.tiene_stock_suficiente(cantidad):
                raise serializers.ValidationError({
                    "cantidad": f"Stock insuficiente. Disponible: {producto.stock_disponible_real}, Solicitado: {cantidad}"
                })

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
