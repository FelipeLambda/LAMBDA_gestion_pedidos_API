from rest_framework import serializers
from .models import Pago
from Pedidos.models import Pedido


class PagoSerializer(serializers.ModelSerializer):
    pedido_numero = serializers.CharField(source='pedido.numero_orden', read_only=True)
    validado_por_nombre = serializers.CharField(source='validado_por.nombre', read_only=True)
    monto_pendiente = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id', 'pedido', 'pedido_numero',
            'monto', 'estado_pago', 'metodo_pago',
            'referencia_pago', 'fecha_pago',
            'validado_por', 'validado_por_nombre',
            'observaciones', 'monto_pendiente',
            'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]
        read_only_fields = [
            'id', 'validado_por', 'fecha_creacion', 'fecha_actualizacion', 'estado'
        ]


class RegistrarPagoSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField(required=True)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0.01)
    metodo_pago = serializers.ChoiceField(
        choices=['TRANSFERENCIA', 'TARJETA', 'EFECTIVO', 'CHEQUE', 'OTRO'],
        required=True
    )
    referencia_pago = serializers.CharField(required=False, allow_blank=True, max_length=100)
    fecha_pago = serializers.DateTimeField(required=True)
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_pedido_id(self, value):
        try:
            pedido = Pedido.objects.get(pk=value, estado=True)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError("Pedido no encontrado o inactivo.")

        if pedido.estado_pedido not in ['PENDIENTE_PAGO', 'PAGO_CONFIRMADO']:
            raise serializers.ValidationError(
                "Solo se pueden registrar pagos en pedidos PENDIENTE_PAGO o PAGO_CONFIRMADO."
            )

        return value

    def validate(self, attrs):
        pedido_id = attrs.get('pedido_id')
        monto = attrs.get('monto')

        pedido = Pedido.objects.get(pk=pedido_id)

        total_pagado = pedido.pagos.filter(
            estado=True,
            estado_pago__in=['COMPLETADO', 'PARCIAL']
        ).aggregate(total=serializers.models.Sum('monto'))['total'] or 0

        monto_pendiente = pedido.total - total_pagado

        if monto > monto_pendiente:
            raise serializers.ValidationError({
                'monto': f'El monto excede el pendiente ({monto_pendiente:.2f}).'
            })

        return attrs


class ValidarPagoSerializer(serializers.Serializer):
    estado_pago = serializers.ChoiceField(
        choices=['COMPLETADO', 'RECHAZADO'],
        required=True
    )
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate(self, attrs):
        if attrs.get('estado_pago') == 'RECHAZADO' and not attrs.get('observaciones'):
            raise serializers.ValidationError({
                "observaciones": "Debe proporcionar observaciones al rechazar un pago."
            })
        return attrs
