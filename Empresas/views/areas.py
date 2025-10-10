from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Empresas.models import Area
from Empresas.serializers import AreaSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_grupos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)
from Usuarios.models import Grupos


class AreaListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        areas = self.filtrar_por_empresa(request, Area.activos.all())
        serializer = AreaSerializer(areas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request):
        serializer = AreaSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Área creada exitosamente',
            'area': serializer.data
        }, status=status.HTTP_201_CREATED)


class AreaDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def get(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        serializer = AreaSerializer(area)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        serializer = AreaSerializer(area, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Área actualizada exitosamente',
            'area': serializer.data
        }, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def delete(self, request, pk):
        area, error = self.obtener_objeto_o_404(Area, pk)
        if error:
            return error

        area.soft_delete()
        return Response({
            'mensaje': 'Área desactivada exitosamente'
        }, status=status.HTTP_200_OK)
