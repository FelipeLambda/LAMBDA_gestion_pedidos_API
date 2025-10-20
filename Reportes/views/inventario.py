from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Inventario.models import MovimientoInventario
from Productos.models import Producto
from Reportes.serializers import FiltroReporteInventarioSerializer, FiltroReporteSerializer
from Reportes.utils import ReporteExcelGenerator, ReporteCSVGenerator
from Reportes.utils_pdf import ReportePDFGenerator
from LAMBDA_gestion_pedidos_API.utils import requiere_permisos
from Usuarios.models import Grupos


class ExportarInventarioAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('reportes.exportar_inventario')
    def get(self, request):
        """Exporta movimientos de inventario en formato Excel o CSV"""
        serializer = FiltroReporteInventarioSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        movimientos = MovimientoInventario.objects.select_related(
            'producto', 'usuario_responsable', 'pedido'
        )

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            movimientos = movimientos.filter(usuario_responsable__empresa=usuario.empresa)

        if filtros.get('fecha_desde'):
            movimientos = movimientos.filter(fecha_creacion__gte=filtros['fecha_desde'])

        if filtros.get('fecha_hasta'):
            movimientos = movimientos.filter(fecha_creacion__lte=filtros['fecha_hasta'])

        if filtros.get('tipo_movimiento'):
            movimientos = movimientos.filter(tipo_movimiento=filtros['tipo_movimiento'])

        if filtros.get('producto_id'):
            movimientos = movimientos.filter(producto_id=filtros['producto_id'])

        movimientos = movimientos.filter(estado=True)

        headers = [
            'ID',
            'Tipo Movimiento',
            'Producto',
            'SKU',
            'Cantidad',
            'Usuario Responsable',
            'Pedido',
            'Observaciones',
            'Fecha',
        ]

        datos = []
        for mov in movimientos:
            datos.append([
                mov.id,
                mov.get_tipo_movimiento_display(),
                mov.producto.nombre,
                mov.producto.sku,
                mov.cantidad,
                mov.usuario_responsable.nombre,
                mov.pedido.numero_orden if mov.pedido else 'N/A',
                mov.observaciones or '',
                mov.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            ])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Inventario', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator('Reporte de Movimientos de Inventario', headers, datos, orientacion='landscape')
        else:
            generator = ReporteExcelGenerator('Reporte_Inventario', headers, datos)

        return generator.generar()


class ExportarStockProductosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('reportes.exportar_stock')
    def get(self, request):
        """Exporta stock de productos en formato Excel o CSV"""
        serializer = FiltroReporteSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        productos = Producto.objects.select_related('categoria').filter(estado=True)

        headers = [
            'ID',
            'SKU',
            'Nombre',
            'Categoría',
            'Precio',
            'Stock Disponible',
            'Stock Reservado',
            'Stock Disponible Real',
            'Umbral Mínimo',
            'Stock Bajo',
        ]

        datos = []
        for prod in productos:
            datos.append([
                prod.id,
                prod.sku,
                prod.nombre,
                prod.categoria.nombre if prod.categoria else 'Sin categoría',
                f"{prod.precio:.2f}",
                prod.stock_disponible,
                prod.stock_reservado,
                prod.stock_disponible_real,
                prod.umbral_minimo,
                'Sí' if prod.stock_bajo else 'No',
            ])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Stock_Productos', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator('Reporte de Stock de Productos', headers, datos)
        else:
            generator = ReporteExcelGenerator('Reporte_Stock_Productos', headers, datos)

        return generator.generar()
