from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud
from Solicitudes.serializers import SolicitudSerializer, ValidarSolicitudSerializer
from LAMBDA_gestion_pedidos_API.utils import manejar_errores_db
from LAMBDA_gestion_pedidos_API.utils.decoradores import requiere_permiso


class ValidarSolicitudBaseAPIView(APIView):
    """
    Clase base abstracta para validaciones de solicitudes.
    """
    permission_classes = [IsAuthenticated]

    estado_requerido = None
    validador_field = None
    fecha_validacion_field = None
    observaciones_field = None
    estado_aprobado = None
    mensaje_aprobado = None
    mensaje_rechazado = None

    def validar_solicitud(self, request, pk):
        try:
            solicitud = Solicitud.objects.get(pk=pk)

            if solicitud.estado_solicitud != self.estado_requerido:
                return Response(
                    {'error': f'La solicitud debe estar en estado {self.get_nombre_estado_requerido()}. Estado actual: {solicitud.get_estado_solicitud_display()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ValidarSolicitudSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            aprobado = serializer.validated_data['aprobado']
            observaciones = serializer.validated_data.get('observaciones', '')

            setattr(solicitud, self.validador_field, request.user)
            setattr(solicitud, self.fecha_validacion_field, timezone.now())
            setattr(solicitud, self.observaciones_field, observaciones)

            if aprobado:
                solicitud.estado_solicitud = self.estado_aprobado
                mensaje = self.mensaje_aprobado
            else:
                solicitud.estado_solicitud = 'RECHAZADA'
                mensaje = self.mensaje_rechazado

            solicitud.save()

            return Response({
                'mensaje': mensaje,
                'solicitud': SolicitudSerializer(solicitud).data
            }, status=status.HTTP_200_OK)

        except Solicitud.DoesNotExist:
            return Response({'error': 'Solicitud no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def get_nombre_estado_requerido(self):
        estados_map = dict(Solicitud.ESTADOS_SOLICITUD)
        return estados_map.get(self.estado_requerido, self.estado_requerido)


class ValidarSolicitudFinancieroAPIView(ValidarSolicitudBaseAPIView):

    estado_requerido = 'PENDIENTE'
    validador_field = 'validador_financiero'
    fecha_validacion_field = 'fecha_validacion_financiero'
    observaciones_field = 'observaciones_financiero'
    estado_aprobado = 'VALIDADA_FINANCIERO'
    mensaje_aprobado = 'Solicitud validada exitosamente por Financiero'
    mensaje_rechazado = 'Solicitud rechazada por Financiero'

    @requiere_permiso('Solicitudes.validar_financiero')
    @manejar_errores_db
    def post(self, request, pk):
        return self.validar_solicitud(request, pk)


class ValidarSolicitudAbastecimientoAPIView(ValidarSolicitudBaseAPIView):

    estado_requerido = 'VALIDADA_FINANCIERO'
    validador_field = 'validador_abastecimiento'
    fecha_validacion_field = 'fecha_validacion_abastecimiento'
    observaciones_field = 'observaciones_abastecimiento'
    estado_aprobado = 'APROBADA'
    mensaje_aprobado = 'Solicitud aprobada completamente. Puede convertirse en pedido.'
    mensaje_rechazado = 'Solicitud rechazada por Abastecimiento'

    @requiere_permiso('Solicitudes.validar_abastecimiento')
    @manejar_errores_db
    def post(self, request, pk):
        return self.validar_solicitud(request, pk)
