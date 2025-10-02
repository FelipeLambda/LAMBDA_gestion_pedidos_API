from django.db import models as django_models
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Productos.models import Producto
from Productos.serializers import (
    ProductoSerializer, ProductoListSerializer,
    ProductoCreateUpdateSerializer
)
from LAMBDA_gestion_pedidos_API.utils import requiere_admin_sistema


class ProductoListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista todos los productos activos.
        Disponible para todos los usuarios autenticados.
        """
        productos = Producto.objects.filter(estado=True)

        categoria_id = request.query_params.get('categoria')
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        stock_bajo = request.query_params.get('stock_bajo')
        if stock_bajo and stock_bajo.lower() == 'true':
            productos = [p for p in productos if p.stock_bajo]
            serializer = ProductoListSerializer(productos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        buscar = request.query_params.get('buscar')
        if buscar:
            productos = productos.filter(
                django_models.Q(nombre__icontains=buscar) |
                django_models.Q(sku__icontains=buscar)
            )

        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_admin_sistema
    def post(self, request):
        """
        Crea un nuevo producto.
        """
        serializer = ProductoCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.save()
            return Response({
                'mensaje': 'Producto creado exitosamente',
                'producto': ProductoSerializer(producto).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductoDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Obtiene el detalle de un producto.
        """
        try:
            producto = Producto.objects.get(pk=pk)
            serializer = ProductoSerializer(producto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_sistema
    def put(self, request, pk):
        """
        Actualiza un producto.
        """
        try:
            producto = Producto.objects.get(pk=pk)

            if 'stock_disponible' in request.data:
                return Response({
                    'error': 'El stock no puede modificarse directamente. Use el módulo de Inventarios.'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = ProductoCreateUpdateSerializer(producto, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'mensaje': 'Producto actualizado exitosamente',
                    'producto': ProductoSerializer(producto).data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_sistema
    def delete(self, request, pk):
        """
        Desactiva un producto (soft delete).
        """
        try:
            producto = Producto.objects.get(pk=pk)
            producto.estado = False
            producto.save()
            return Response({
                'mensaje': 'Producto desactivado exitosamente'
            }, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ProductoAlertasStockAPIView(APIView):
    """
    Retorna productos con stock bajo (stock_disponible < umbral_minimo).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lista productos con stock bajo.
        """
        if not request.user.es_admin_sistema:
            return Response({
                'error': 'Solo administradores del sistema pueden ver alertas de stock.'
            }, status=status.HTTP_403_FORBIDDEN)

        productos = Producto.objects.filter(estado=True)
        productos_con_alerta = [p for p in productos if p.stock_bajo]

        serializer = ProductoSerializer(productos_con_alerta, many=True)
        return Response({
            'total_alertas': len(productos_con_alerta),
            'productos': serializer.data
        }, status=status.HTTP_200_OK)
