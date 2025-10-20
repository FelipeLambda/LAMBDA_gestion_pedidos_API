from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Empresas.models import Area
from Empresas.serializers import AreaSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_permisos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)


class AreaListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('areas.listar')
    def get(self, request):
        areas = self.filtrar_por_empresa(request, Area.activos.all())
        serializer = AreaSerializer(areas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('areas.crear')
    def post(self, request):
        empresa_id = request.data.get('empresa')

        if not self._puede_crear_area_para_empresa(request.user, empresa_id):
            return Response(
                {'error': 'No tiene permisos para crear áreas para esta empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AreaSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Área creada exitosamente',
            'area': serializer.data
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def _puede_crear_area_para_empresa(usuario, empresa_id):
        from Usuarios.models import Grupos

        if usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return True

        if usuario.empresa and usuario.empresa.id == empresa_id:
            return True

        return False


class AreaDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('areas.listar')
    @manejar_errores_db
    def get(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        if not self._puede_ver_area(request.user, area):
            return Response(
                {'error': 'No tiene permisos para ver esta área'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AreaSerializer(area)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('areas.editar')
    @manejar_errores_db
    def put(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        if not self._puede_editar_area(request.user, area):
            return Response(
                {'error': 'No tiene permisos para editar esta área'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AreaSerializer(area, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Área actualizada exitosamente',
            'area': serializer.data
        }, status=status.HTTP_200_OK)

    @requiere_permisos('areas.eliminar')
    @manejar_errores_db
    def delete(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        if not self._puede_eliminar_area(request.user, area):
            return Response(
                {'error': 'No tiene permisos para eliminar esta área'},
                status=status.HTTP_403_FORBIDDEN
            )

        area.soft_delete()
        return Response({
            'mensaje': 'Área desactivada exitosamente'
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _es_admin_sistema(usuario):
        from Usuarios.models import Grupos
        return usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists()

    def _puede_ver_area(self, usuario, area):
        if self._es_admin_sistema(usuario):
            return True
        if usuario.empresa and area.empresa and usuario.empresa.id == area.empresa.id:
            return True
        return False

    def _puede_editar_area(self, usuario, area):
        from Usuarios.models import Grupos
        if self._es_admin_sistema(usuario):
            return True
        if usuario.empresa and area.empresa and usuario.empresa.id == area.empresa.id:
            if usuario.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
                return True
        return False

    def _puede_eliminar_area(self, usuario, area):
        return self._puede_editar_area(usuario, area)
