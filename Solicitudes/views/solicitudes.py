from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud
from Solicitudes.serializers import (
    SolicitudSerializer,
    CrearSolicitudSerializer
)
from Usuarios.models import Grupos
from LAMBDA_gestion_pedidos_API.utils import (
    FiltradoEmpresaMixin,
    PermisosPorEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db,
    requiere_permisos
)


class SolicitudListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            solicitudes = Solicitud.objects.all()
        elif usuario.roles.filter(nombre__in=[Grupos.ADMIN_EMPRESA, Grupos.VALIDADOR_FINANCIERO, Grupos.VALIDADOR_ABASTECIMIENTO]).exists():
            solicitudes = self.filtrar_por_empresa(request, Solicitud.objects.all())
        else:
            solicitudes = Solicitud.objects.filter(solicitante=usuario)

        serializer = SolicitudSerializer(solicitudes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('solicitudes.crear')
    @manejar_errores_db
    def post(self, request):
        serializer = CrearSolicitudSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        solicitud = serializer.save()
        return Response({
            'mensaje': 'Solicitud creada exitosamente',
            'solicitud': SolicitudSerializer(solicitud).data
        }, status=status.HTTP_201_CREATED)


class SolicitudDetailAPIView(FiltradoEmpresaMixin, PermisosPorEmpresaMixin, ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        solicitud, error = self.obtener_objeto_o_404(Solicitud, pk)
        if error:
            return error

        puede_ver, mensaje_error = self.puede_ver_recurso(
            request.user,
            solicitud,
            roles_adicionales=[Grupos.VALIDADOR_FINANCIERO, Grupos.VALIDADOR_ABASTECIMIENTO]
        )
        if not puede_ver:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        serializer = SolicitudSerializer(solicitud)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('solicitudes.eliminar')
    @manejar_errores_db
    def delete(self, request, pk):
        solicitud, error = self.obtener_objeto_o_404(Solicitud, pk)
        if error:
            return error

        if solicitud.estado_solicitud != Solicitud.Estados.PENDIENTE_ABASTECIMIENTO:
            return Response(
                {'error': 'Solo se pueden eliminar solicitudes en estado PENDIENTE_ABASTECIMIENTO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        puede_eliminar, mensaje_error = self.puede_eliminar_recurso(request.user, solicitud)
        if not puede_eliminar:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        solicitud.soft_delete()

        return Response(
            {'mensaje': 'Solicitud eliminada exitosamente'},
            status=status.HTTP_200_OK
        )
