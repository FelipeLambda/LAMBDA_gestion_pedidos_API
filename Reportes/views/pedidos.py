from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pedidos.models import Pedido
from Reportes.serializers import FiltroReportePedidosSerializer
from Reportes.utils import ReporteExcelGenerator, ReporteCSVGenerator
from LAMBDA_gestion_pedidos_API.utils import requiere_grupos
from Usuarios.models import Grupos


class ExportarPedidosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        serializer = FiltroReportePedidosSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        pedidos = Pedido.objects.select_related(
            'empresa', 'solicitante', 'solicitud'
        ).prefetch_related('detalles__producto')

        usuario = request.user
        if not usuario.is_superuser and not usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            pedidos = pedidos.filter(empresa=usuario.empresa)

        if filtros.get('empresa_id'):
            pedidos = pedidos.filter(empresa_id=filtros['empresa_id'])

        if filtros.get('fecha_desde'):
            pedidos = pedidos.filter(fecha_creacion__gte=filtros['fecha_desde'])

        if filtros.get('fecha_hasta'):
            pedidos = pedidos.filter(fecha_creacion__lte=filtros['fecha_hasta'])

        if filtros.get('estado'):
            pedidos = pedidos.filter(estado_pedido=filtros['estado'])

        pedidos = pedidos.filter(estado=True)

        headers = [
            'ID',
            'Número de Orden',
            'Empresa',
            'Solicitante',
            'Email Solicitante',
            'Estado',
            'Total',
            'Cantidad Items',
            'Solicitud ID',
            'Observaciones',
            'Fecha Completado',
            'Fecha Creación',
        ]

        datos = []
        for pedido in pedidos:
            datos.append([
                pedido.id,
                pedido.numero_orden,
                pedido.empresa.nombre,
                pedido.solicitante.nombre,
                pedido.solicitante.email,
                pedido.get_estado_pedido_display(),
                f"{pedido.total:.2f}",
                pedido.cantidad_items,
                pedido.solicitud.id,
                pedido.observaciones or '',
                pedido.fecha_completado.strftime('%Y-%m-%d %H:%M') if pedido.fecha_completado else 'N/A',
                pedido.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            ])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Pedidos', headers, datos)
        else:
            generator = ReporteExcelGenerator('Reporte_Pedidos', headers, datos)

        return generator.generar()
