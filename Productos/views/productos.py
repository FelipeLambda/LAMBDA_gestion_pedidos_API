from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Productos.models import Producto
from Productos.serializers import (
    ProductoSerializer, ProductoListSerializer,
    ProductoCreateUpdateSerializer
)
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_permisos,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)
from Usuarios.models import Grupos


class ProductoListCreateAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todos los productos activos.
        """
        stock_bajo = request.query_params.get('stock_bajo')
        if stock_bajo and stock_bajo.lower() == 'true':
            productos = Producto.objects.con_stock_bajo()
        else:
            productos = Producto.activos.all()

        categoria_id = request.query_params.get('categoria')
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        buscar = request.query_params.get('buscar')
        if buscar:
            productos = productos.filter(
                Q(nombre__icontains=buscar) |
                Q(sku__icontains=buscar)
            )

        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    def post(self, request):
        """
        Crea un nuevo producto.
        """
        serializer = ProductoCreateUpdateSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        producto = serializer.save()
        return Response({
            'mensaje': 'Producto creado exitosamente',
            'producto': ProductoSerializer(producto).data
        }, status=status.HTTP_201_CREATED)


class ProductoDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        """
        Obtiene el detalle de un producto.
        """
        producto, error = self.obtener_objeto_o_404(Producto, pk)
        if error:
            return error

        serializer = ProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    @manejar_errores_db
    def put(self, request, pk):
        """
        Actualiza un producto.
        """
        producto, error = self.obtener_objeto_o_404(Producto, pk)
        if error:
            return error

        if 'stock_disponible' in request.data:
            return Response({
                'error': 'El stock no puede modificarse directamente. Use el módulo de Inventarios.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductoCreateUpdateSerializer(producto, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Producto actualizado exitosamente',
            'producto': ProductoSerializer(producto).data
        }, status=status.HTTP_200_OK)

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    @manejar_errores_db
    def delete(self, request, pk):
        """
        Desactiva un producto (soft delete).
        """
        producto, error = self.obtener_objeto_o_404(Producto, pk)
        if error:
            return error

        producto.soft_delete()
        return Response({
            'mensaje': 'Producto desactivado exitosamente'
        }, status=status.HTTP_200_OK)


class ProductoAlertasStockAPIView(APIView):
    """
    Retorna productos con stock bajo (stock_disponible < umbral_minimo).
    """
    permission_classes = [IsAuthenticated]

    @requiere_permisos("productos.crear", "productos.editar", "productos.eliminar", "categorias.crear", "categorias.editar", "categorias.eliminar", "productos.ver_alertas_stock")
    def get(self, request):
        """
        Lista productos con stock bajo.
        """
        productos_con_alerta = Producto.objects.con_stock_bajo()

        serializer = ProductoSerializer(productos_con_alerta, many=True)
        return Response({
            'total_alertas': productos_con_alerta.count(),
            'productos': serializer.data
        }, status=status.HTTP_200_OK)
