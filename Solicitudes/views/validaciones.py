from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud
from Solicitudes.serializers import SolicitudSerializer, ValidarSolicitudSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    manejar_errores_db,
    ObjetoDetailMixin,
    SerializerValidationMixin
)
from LAMBDA_gestion_pedidos_API.utils.decoradores import requiere_permiso


class ValidarSolicitudBaseAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
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
        solicitud, error = self.obtener_objeto_o_404(Solicitud, pk, usar_soft_delete=False)
        if error:
            return error

        if solicitud.estado_solicitud != self.estado_requerido:
            return Response(
                {'error': f'La solicitud debe estar en estado {self.get_nombre_estado_requerido()}. Estado actual: {solicitud.get_estado_solicitud_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ValidarSolicitudSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        aprobado = serializer.validated_data['aprobado']
        observaciones = serializer.validated_data.get('observaciones', '')

        setattr(solicitud, self.validador_field, request.user)
        setattr(solicitud, self.fecha_validacion_field, timezone.now())
        setattr(solicitud, self.observaciones_field, observaciones)

        if aprobado:
            solicitud.estado_solicitud = self.estado_aprobado
            mensaje = self.mensaje_aprobado
        else:
            solicitud.estado_solicitud = Solicitud.Estados.RECHAZADA
            mensaje = self.mensaje_rechazado

        solicitud.save()

        return Response({
            'mensaje': mensaje,
            'solicitud': SolicitudSerializer(solicitud).data
        }, status=status.HTTP_200_OK)

    def get_nombre_estado_requerido(self):
        return Solicitud.Estados(self.estado_requerido).label


class ValidarSolicitudAbastecimientoAPIView(ValidarSolicitudBaseAPIView):

    estado_requerido = Solicitud.Estados.PENDIENTE_ABASTECIMIENTO
    validador_field = 'validador_abastecimiento'
    fecha_validacion_field = 'fecha_validacion_abastecimiento'
    observaciones_field = 'observaciones_abastecimiento'
    estado_aprobado = Solicitud.Estados.PENDIENTE_FINANZAS
    mensaje_aprobado = 'Solicitud validada exitosamente por Abastecimiento. Pasa a validación financiera.'
    mensaje_rechazado = 'Solicitud rechazada por Abastecimiento'

    @requiere_permiso('Solicitudes.validar_abastecimiento')
    @manejar_errores_db
    def post(self, request, pk):
        return self.validar_solicitud(request, pk)


class ValidarSolicitudFinancieroAPIView(ValidarSolicitudBaseAPIView):

    estado_requerido = Solicitud.Estados.PENDIENTE_FINANZAS
    validador_field = 'validador_financiero'
    fecha_validacion_field = 'fecha_validacion_financiero'
    observaciones_field = 'observaciones_financiero'
    estado_aprobado = Solicitud.Estados.LISTO_PARA_COMPRA
    mensaje_aprobado = 'Solicitud lista para compra. Puede convertirse en pedido.'
    mensaje_rechazado = 'Solicitud rechazada por Financiero'

    @requiere_permiso('Solicitudes.validar_financiero')
    @manejar_errores_db
    def post(self, request, pk):
        return self.validar_solicitud(request, pk)
