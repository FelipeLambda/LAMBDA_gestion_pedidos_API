from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud, DetalleSolicitud
from Solicitudes.serializers import SolicitudSerializer, ModificarSolicitudAbastecimientoSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    manejar_errores_db,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    requiere_permisos
)


class ModificarSolicitudAbastecimientoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('solicitudes.validar_abastecimiento')
    @manejar_errores_db
    def patch(self, request, pk):
        solicitud, error = self.obtener_objeto_o_404(Solicitud, pk)
        if error:
            return error

        if solicitud.estado_solicitud != Solicitud.Estados.PENDIENTE_ABASTECIMIENTO:
            return Response(
                {'error': f'Solo se pueden modificar solicitudes en estado PENDIENTE_ABASTECIMIENTO. Estado actual: {solicitud.get_estado_solicitud_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ModificarSolicitudAbastecimientoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        detalles_modificados = serializer.validated_data['detalles_modificados']
        observaciones_modificacion = serializer.validated_data['observaciones']

        detalles_antiguos = list(solicitud.detalles.filter(estado=True).values(
            'id', 'producto__nombre', 'cantidad'
        ))

        for detalle in solicitud.detalles.all():
            detalle.soft_delete()

        for detalle_data in detalles_modificados:
            producto = detalle_data['producto']
            DetalleSolicitud.objects.create(
                solicitud=solicitud,
                producto=producto,
                cantidad=detalle_data['cantidad'],
                precio_unitario=producto.precio
            )

        historial_cambios = f"\n\n[MODIFICACIÓN POR ABASTECIMIENTO - {timezone.now().strftime('%Y-%m-%d %H:%M')}]\n"
        historial_cambios += f"Modificado por: {request.user.nombre}\n"
        historial_cambios += f"Motivo: {observaciones_modificacion}\n"
        historial_cambios += f"Detalles anteriores: {detalles_antiguos}\n"

        solicitud.observaciones_abastecimiento = (solicitud.observaciones_abastecimiento or '') + historial_cambios
        solicitud.save()

        return Response({
            'mensaje': 'Solicitud modificada exitosamente por validador de abastecimiento',
            'solicitud': SolicitudSerializer(solicitud).data
        }, status=status.HTTP_200_OK)
