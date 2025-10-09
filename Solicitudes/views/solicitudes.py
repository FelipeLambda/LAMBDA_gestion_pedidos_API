from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud
from Solicitudes.serializers import (
    SolicitudSerializer,
    CrearSolicitudSerializer
)
from LAMBDA_gestion_pedidos_API.utils import (
    FiltradoEmpresaMixin,
    PermisosPorEmpresaMixin,
    manejar_errores_db
)
from LAMBDA_gestion_pedidos_API.utils.decoradores import requiere_grupos
from Usuarios.models import Grupos


class SolicitudListCreateAPIView(FiltradoEmpresaMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            solicitudes = Solicitud.objects.all()
        elif usuario.groups.filter(name__in=[Grupos.ADMIN_EMPRESA, Grupos.VALIDADOR_FINANCIERO, Grupos.VALIDADOR_ABASTECIMIENTO]).exists():
            solicitudes = self.filtrar_por_empresa(request, Solicitud.objects.all())
        else:
            solicitudes = Solicitud.objects.filter(solicitante=usuario)

        serializer = SolicitudSerializer(solicitudes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.SOLICITANTE, Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def post(self, request):
        serializer = CrearSolicitudSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            solicitud = serializer.save()
            return Response({
                'mensaje': 'Solicitud creada exitosamente',
                'solicitud': SolicitudSerializer(solicitud).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SolicitudDetailAPIView(FiltradoEmpresaMixin, PermisosPorEmpresaMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        try:
            solicitud = Solicitud.objects.get(pk=pk)

            puede_ver, mensaje_error = self.puede_ver_recurso(
                request.user,
                solicitud,
                grupos_adicionales=[Grupos.VALIDADOR_FINANCIERO, Grupos.VALIDADOR_ABASTECIMIENTO]
            )
            if not puede_ver:
                return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

            serializer = SolicitudSerializer(solicitud)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Solicitud.DoesNotExist:
            return Response({'error': 'Solicitud no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def delete(self, request, pk):
        try:
            solicitud = Solicitud.objects.get(pk=pk)

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

        except Solicitud.DoesNotExist:
            return Response({'error': 'Solicitud no encontrada'}, status=status.HTTP_404_NOT_FOUND)
