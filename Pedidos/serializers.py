from rest_framework import serializers
from .models import Pedido, DetallePedido
from Solicitudes.models import Solicitud
from Base.serializers import DetalleBaseSerializer


class DetallePedidoSerializer(DetalleBaseSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_sku',
            'cantidad', 'precio_unitario', 'subtotal',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class DetallePedidoCreateSerializer(DetalleBaseSerializer):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad']


class PedidoSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    solicitante_nombre = serializers.CharField(source='solicitante.nombre', read_only=True)
    solicitante_email = serializers.CharField(source='solicitante.email', read_only=True)
    solicitud_id = serializers.IntegerField(source='solicitud.id', read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cantidad_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'numero_orden', 'solicitud', 'solicitud_id',
            'empresa', 'empresa_nombre',
            'solicitante', 'solicitante_nombre', 'solicitante_email',
            'estado_pedido', 'observaciones', 'fecha_completado',
            'detalles', 'total', 'cantidad_items',
            'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]
        read_only_fields = [
            'id', 'numero_orden', 'solicitante', 'empresa',
            'fecha_completado', 'fecha_creacion', 'fecha_actualizacion'
        ]


class CrearPedidoSerializer(serializers.Serializer):
    solicitud_id = serializers.IntegerField(required=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate_solicitud_id(self, value):
        try:
            solicitud = Solicitud.objects.get(pk=value, estado=True)
        except Solicitud.DoesNotExist:
            raise serializers.ValidationError("Solicitud no encontrada o inactiva.")

        if solicitud.estado_solicitud != 'APROBADA':
            raise serializers.ValidationError("Solo se pueden convertir solicitudes aprobadas en pedidos.")

        if solicitud.pedidos.filter(estado=True).exists():
            raise serializers.ValidationError("Esta solicitud ya tiene un pedido activo asociado.")

        return value


class ActualizarEstadoPedidoSerializer(serializers.Serializer):
    estado_pedido = serializers.ChoiceField(
        choices=['PENDIENTE_PAGO', 'PAGO_CONFIRMADO', 'EN_DESPACHO', 'COMPLETADO', 'CANCELADO'],
        required=True
    )
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate(self, attrs):
        if attrs.get('estado_pedido') == 'CANCELADO' and not attrs.get('observaciones'):
            raise serializers.ValidationError({
                "observaciones": "Debe proporcionar observaciones al cancelar un pedido."
            })
        return attrs


class EditarPedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoCreateSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Pedido
        fields = ['observaciones', 'detalles']

    def validate_detalles(self, value):
        if value:
            productos_ids = [detalle['producto'].id for detalle in value]
            if len(productos_ids) != len(set(productos_ids)):
                raise serializers.ValidationError("No se pueden repetir productos en el mismo pedido.")
        return value

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop('detalles', None)

        instance.observaciones = validated_data.get('observaciones', instance.observaciones)
        instance.save()

        if detalles_data is not None:
            for detalle in instance.detalles.all():
                detalle.soft_delete()
            for detalle_data in detalles_data:
                producto = detalle_data['producto']
                DetallePedido.objects.create(
                    pedido=instance,
                    producto=producto,
                    cantidad=detalle_data['cantidad'],
                    precio_unitario=producto.precio
                )

        return instance
