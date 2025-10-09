from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Productos.models import Categoria
from Productos.serializers import CategoriaSerializer
from LAMBDA_gestion_pedidos_API.utils import requiere_grupos, manejar_errores_db
from Usuarios.models import Grupos

class CategoriaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todas las categorías activas.
        """
        categorias = Categoria.activos.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    def post(self, request):
        """
        Crea una nueva categoría.
        """
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'mensaje': 'Categoría creada exitosamente',
                'categoria': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        """
        Obtiene el detalle de una categoría.
        """
        try:
            categoria = Categoria.objects.get(pk=pk)
            serializer = CategoriaSerializer(categoria)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Categoria.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        """
        Actualiza una categoría.
        """
        try:
            categoria = Categoria.objects.get(pk=pk)
            serializer = CategoriaSerializer(categoria, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'mensaje': 'Categoría actualizada exitosamente',
                    'categoria': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Categoria.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def delete(self, request, pk):
        """
        Desactiva una categoría (soft delete).
        """
        try:
            categoria = Categoria.objects.get(pk=pk)
            categoria.soft_delete()
            return Response({
                'mensaje': 'Categoría desactivada exitosamente'
            }, status=status.HTTP_200_OK)
        except Categoria.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'}, status=status.HTTP_404_NOT_FOUND)
