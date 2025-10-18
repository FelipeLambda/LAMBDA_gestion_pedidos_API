from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Productos.models import Categoria
from Productos.serializers import CategoriaSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_permisos,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)
from Usuarios.models import Grupos

class CategoriaListCreateAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todas las categorías activas.
        """
        categorias = Categoria.activos.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    def post(self, request):
        """
        Crea una nueva categoría.
        """
        serializer = CategoriaSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Categoría creada exitosamente',
            'categoria': serializer.data
        }, status=status.HTTP_201_CREATED)


class CategoriaDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        """
        Obtiene el detalle de una categoría.
        """
        categoria, error = self.obtener_objeto_o_404(Categoria, pk)
        if error:
            return error

        serializer = CategoriaSerializer(categoria)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    @manejar_errores_db
    def put(self, request, pk):
        """
        Actualiza una categoría.
        """
        categoria, error = self.obtener_objeto_o_404(Categoria, pk)
        if error:
            return error

        serializer = CategoriaSerializer(categoria, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Categoría actualizada exitosamente',
            'categoria': serializer.data
        }, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    @manejar_errores_db
    def delete(self, request, pk):
        """
        Desactiva una categoría (soft delete).
        """
        categoria, error = self.obtener_objeto_o_404(Categoria, pk)
        if error:
            return error

        categoria.soft_delete()
        return Response({
            'mensaje': 'Categoría desactivada exitosamente'
        }, status=status.HTTP_200_OK)
