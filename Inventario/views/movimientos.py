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
from LAMBDA_gestion_pedidos_API.utils import (
    manejar_errores_db,
    requiere_permisos,
    ObjetoDetailMixin,
    SerializerValidationMixin
)
from Usuarios.models import Grupos


class MovimientoInventarioListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos("inventario.listar_movimientos", "inventario.registrar_movimiento", "inventario.exportar")
    def get(self, request):
        movimientos = MovimientoInventario.objects.all()

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            movimientos = movimientos.filter(
                Q(pedido__empresa=usuario.empresa) | Q(pedido__isnull=True, usuario_responsable__empresa=usuario.empresa)
            )

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


class RegistrarMovimientoAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos("inventario.listar_movimientos", "inventario.registrar_movimiento", "inventario.exportar")
    @manejar_errores_db
    def post(self, request):
        serializer = RegistrarMovimientoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        tipo_movimiento = serializer.validated_data['tipo_movimiento']
        producto = serializer.validated_data['producto']
        cantidad = serializer.validated_data['cantidad']
        observaciones = serializer.validated_data.get('observaciones', '')

        movimiento = MovimientoInventario.objects.create(
            tipo_movimiento=tipo_movimiento,
            producto=producto,
            cantidad=cantidad,
            usuario_responsable=request.user,
            observaciones=observaciones
        )

        if movimiento.es_incremento:
            producto.stock_disponible += cantidad
        else:
            producto.stock_disponible -= cantidad
        producto.save()

        return Response({
            'mensaje': f'{movimiento.get_tipo_movimiento_display()} registrado exitosamente',
            'movimiento': MovimientoInventarioSerializer(movimiento).data
        }, status=status.HTTP_201_CREATED)


class StockProductoAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        producto, error = self.obtener_objeto_o_404(Producto, pk)
        if error:
            return error

        serializer = StockProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)
