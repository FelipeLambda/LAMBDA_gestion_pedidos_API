from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Inventario.models import MovimientoInventario
from Inventario.serializers import (
    MovimientoInventarioSerializer,
    RegistrarMovimientoSerializer,
    StockProductoSerializer
)
from Productos.models import Producto
from LAMBDA_gestion_pedidos_API.utils import manejar_errores_db, requiere_grupos
from Usuarios.models import Grupos


class MovimientoInventarioListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    def get(self, request):
        movimientos = MovimientoInventario.objects.all()

        tipo_movimiento = request.query_params.get('tipo_movimiento', None)
        if tipo_movimiento:
            movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)

        producto_id = request.query_params.get('producto_id', None)
        if producto_id:
            movimientos = movimientos.filter(producto_id=producto_id)

        pedido_id = request.query_params.get('pedido_id', None)
        if pedido_id:
            movimientos = movimientos.filter(pedido_id=pedido_id)

        search = request.query_params.get('search', None)
        if search:
            movimientos = movimientos.filter(
                Q(producto__nombre__icontains=search) |
                Q(producto__sku__icontains=search)
            )

        serializer = MovimientoInventarioSerializer(movimientos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegistrarMovimientoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def post(self, request):
        serializer = RegistrarMovimientoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tipo_movimiento = serializer.validated_data['tipo_movimiento']
        producto = serializer.validated_data['producto']
        cantidad = serializer.validated_data['cantidad']
        observaciones = serializer.validated_data.get('observaciones', '')

        if tipo_movimiento == MovimientoInventario.TiposMovimiento.ENTRADA:
            producto.stock_disponible += cantidad
            producto.save()
        else:
            producto.stock_disponible -= cantidad
            producto.save()

        movimiento = MovimientoInventario.objects.create(
            tipo_movimiento=tipo_movimiento,
            producto=producto,
            cantidad=cantidad,
            usuario_responsable=request.user,
            observaciones=observaciones
        )

        return Response({
            'mensaje': f'{tipo_movimiento.capitalize()} registrada exitosamente',
            'movimiento': MovimientoInventarioSerializer(movimiento).data
        }, status=status.HTTP_201_CREATED)


class StockProductoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            producto = Producto.objects.get(pk=pk, estado=True)
            serializer = StockProductoSerializer(producto)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Producto.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
