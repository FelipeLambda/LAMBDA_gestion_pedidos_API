from rest_framework import serializers
from Solicitudes.models import Solicitud
from Pedidos.models import Pedido
from Inventario.models import MovimientoInventario


class FiltroReporteSerializer(serializers.Serializer):
    fecha_desde = serializers.DateField(required=False, help_text='Fecha de inicio (YYYY-MM-DD)')
    fecha_hasta = serializers.DateField(required=False, help_text='Fecha de fin (YYYY-MM-DD)')
    empresa_id = serializers.IntegerField(required=False, help_text='ID de la empresa')
    formato = serializers.ChoiceField(
        choices=['excel', 'csv', 'pdf'],
        default='excel',
        help_text='Formato de exportación'
    )

    def validate(self, attrs):
        fecha_desde = attrs.get('fecha_desde')
        fecha_hasta = attrs.get('fecha_hasta')

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise serializers.ValidationError({
                'fecha_desde': 'La fecha de inicio no puede ser mayor a la fecha de fin.'
            })

        return attrs


class FiltroReporteSolicitudesSerializer(FiltroReporteSerializer):
    estado = serializers.ChoiceField(
        choices=Solicitud.Estados.choices,
        required=False,
        help_text='Estado de la solicitud'
    )
    solicitante_id = serializers.IntegerField(required=False, help_text='ID del solicitante')


class FiltroReportePedidosSerializer(FiltroReporteSerializer):
    estado = serializers.ChoiceField(
        choices=Pedido.Estados.choices,
        required=False,
        help_text='Estado del pedido'
    )


class FiltroReporteInventarioSerializer(FiltroReporteSerializer):
    tipo_movimiento = serializers.ChoiceField(
        choices=['ENTRADA', 'SALIDA', 'RESERVA', 'LIBERACION_RESERVA'],
        required=False,
        help_text='Tipo de movimiento'
    )
    producto_id = serializers.IntegerField(required=False, help_text='ID del producto')
