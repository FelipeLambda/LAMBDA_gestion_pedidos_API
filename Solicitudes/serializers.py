from rest_framework import serializers
from .models import Solicitud, DetalleSolicitud
from Base.serializers import DetalleBaseSerializer


class DetalleSolicitudSerializer(DetalleBaseSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleSolicitud
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_sku',
            'cantidad', 'precio_unitario', 'subtotal',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class DetalleSolicitudCreateSerializer(DetalleBaseSerializer):
    class Meta:
        model = DetalleSolicitud
        fields = ['producto', 'cantidad']


class SolicitudSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    solicitante_nombre = serializers.CharField(source='solicitante.nombre', read_only=True)
    solicitante_email = serializers.CharField(source='solicitante.email', read_only=True)
    validador_financiero_nombre = serializers.CharField(source='validador_financiero.nombre', read_only=True)
    validador_abastecimiento_nombre = serializers.CharField(source='validador_abastecimiento.nombre', read_only=True)

    detalles = DetalleSolicitudSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cantidad_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            'id', 'empresa', 'empresa_nombre', 'area', 'area_nombre',
            'solicitante', 'solicitante_nombre', 'solicitante_email',
            'estado_solicitud', 'observaciones',
            'validador_financiero', 'validador_financiero_nombre', 'fecha_validacion_financiero', 'observaciones_financiero',
            'validador_abastecimiento', 'validador_abastecimiento_nombre', 'fecha_validacion_abastecimiento', 'observaciones_abastecimiento',
            'detalles', 'total', 'cantidad_items',
            'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]
        read_only_fields = [
            'id', 'solicitante', 'estado_solicitud',
            'validador_financiero', 'fecha_validacion_financiero', 'observaciones_financiero',
            'validador_abastecimiento', 'fecha_validacion_abastecimiento', 'observaciones_abastecimiento',
            'fecha_creacion', 'fecha_actualizacion'
        ]


class CrearSolicitudSerializer(serializers.ModelSerializer):
    detalles = DetalleSolicitudCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Solicitud
        fields = ['empresa', 'area', 'observaciones', 'detalles']

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un detalle en la solicitud.")

        productos_ids = [detalle['producto'].id for detalle in value]
        if len(productos_ids) != len(set(productos_ids)):
            raise serializers.ValidationError("No se pueden repetir productos en la misma solicitud.")

        return value

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        usuario = self.context['request'].user

        solicitud = Solicitud.objects.create(
            solicitante=usuario,
            **validated_data
        )

        for detalle_data in detalles_data:
            producto = detalle_data['producto']
            DetalleSolicitud.objects.create(
                solicitud=solicitud,
                producto=producto,
                cantidad=detalle_data['cantidad'],
                precio_unitario=producto.precio
            )

        return solicitud


class ValidarSolicitudSerializer(serializers.Serializer):
    aprobado = serializers.BooleanField(required=True)
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate(self, attrs):
        if not attrs.get('aprobado') and not attrs.get('observaciones'):
            raise serializers.ValidationError({
                "observaciones": "Debe proporcionar observaciones al rechazar una solicitud."
            })
        return attrs
