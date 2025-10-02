from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Usuarios.models import Area
from Usuarios.serializers import AreaSerializer
from LAMBDA_gestion_pedidos_API.utils import requiere_admin_empresa


class AreaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.es_admin_sistema:
            areas = Area.objects.filter(estado=True)
        else:
            areas = Area.objects.filter(empresa=request.user.empresa, estado=True)
        serializer = AreaSerializer(areas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_admin_empresa
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

    def get(self, request, pk):
        try:
            area = Area.objects.get(pk=pk)
            serializer = AreaSerializer(area)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Area.DoesNotExist:
            return Response({'error': 'Área no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_empresa
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
