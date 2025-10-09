from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Empresas.models import Area
from Empresas.serializers import AreaSerializer
from LAMBDA_gestion_pedidos_API.utils import requiere_grupos, FiltradoEmpresaMixin, manejar_errores_db
from Usuarios.models import Grupos


class AreaListCreateAPIView(FiltradoEmpresaMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        areas = self.filtrar_por_empresa(request, Area.activos.all())
        serializer = AreaSerializer(areas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request):
        serializer = AreaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'mensaje': 'Área creada exitosamente',
                'area': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AreaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def get(self, request, pk):
        try:
            area = Area.objects.get(pk=pk)
            serializer = AreaSerializer(area)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Area.DoesNotExist:
            return Response({'error': 'Área no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        try:
            area = Area.objects.get(pk=pk)
            serializer = AreaSerializer(area, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'mensaje': 'Área actualizada exitosamente',
                    'area': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Area.DoesNotExist:
            return Response({'error': 'Área no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def delete(self, request, pk):
        try:
            area = Area.objects.get(pk=pk)
            area.soft_delete()
            return Response({
                'mensaje': 'Área desactivada exitosamente'
            }, status=status.HTTP_200_OK)
        except Area.DoesNotExist:
            return Response({'error': 'Área no encontrada'}, status=status.HTTP_404_NOT_FOUND)
