from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pedidos.models import Pedido
from Pagos.models import Pago
from Reportes.serializers import FiltroReporteSerializer
from Reportes.utils import ReporteExcelGenerator, ReporteCSVGenerator
from Reportes.utils_pdf import ReportePDFGenerator
from Usuarios.models import Grupos
from LAMBDA_gestion_pedidos_API.utils import requiere_permisos


class ReporteFacturacionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos("reportes.exportar_pedidos", "reportes.exportar_facturacion", "reportes.exportar_pagos", "reportes.exportar_solicitudes")
    def get(self, request):
        serializer = FiltroReporteSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        pedidos = Pedido.objects.filter(estado=True, estado_pedido=Pedido.Estados.COMPLETADO)

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pedidos = pedidos.filter(empresa=usuario.empresa)

        if filtros.get('empresa_id'):
            pedidos = pedidos.filter(empresa_id=filtros['empresa_id'])

        if filtros.get('fecha_desde'):
            pedidos = pedidos.filter(fecha_completado__gte=filtros['fecha_desde'])

        if filtros.get('fecha_hasta'):
            pedidos = pedidos.filter(fecha_completado__lte=filtros['fecha_hasta'])

        pedidos = pedidos.select_related('empresa', 'solicitante').order_by('-fecha_completado')

        headers = [
            'ID',
            'Número de Orden',
            'Empresa',
            'Solicitante',
            'Tipo de Pago',
            'Total Facturado',
            'Cantidad Items',
            'Fecha Completado',
            'Observaciones'
        ]

        datos = []
        total_facturado = 0
        for pedido in pedidos:
            datos.append([
                pedido.id,
                pedido.numero_orden,
                pedido.empresa.nombre,
                pedido.solicitante.nombre,
                pedido.get_tipo_pago_display(),
                f"${pedido.total:,.2f}",
                pedido.cantidad_items,
                pedido.fecha_completado.strftime('%Y-%m-%d %H:%M'),
                pedido.observaciones or ''
            ])
            total_facturado += pedido.total

        datos.append([])
        datos.append(['', '', '', '', 'TOTAL FACTURADO:', f"${total_facturado:,.2f}", '', '', ''])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Facturacion', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator('Reporte de Facturación', headers, datos, orientacion='landscape')
        else:
            generator = ReporteExcelGenerator('Reporte_Facturacion', headers, datos)

        return generator.generar()


class ReportePagosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos("reportes.exportar_pedidos", "reportes.exportar_facturacion", "reportes.exportar_pagos", "reportes.exportar_solicitudes")
    def get(self, request):
        serializer = FiltroReporteSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        pagos = Pago.objects.filter(estado=True).select_related('pedido__empresa', 'validado_por')

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pagos = pagos.filter(pedido__empresa=usuario.empresa)

        if filtros.get('empresa_id'):
            pagos = pagos.filter(pedido__empresa_id=filtros['empresa_id'])

        if filtros.get('fecha_desde'):
            pagos = pagos.filter(fecha_pago__gte=filtros['fecha_desde'])

        if filtros.get('fecha_hasta'):
            pagos = pagos.filter(fecha_pago__lte=filtros['fecha_hasta'])

        pagos = pagos.order_by('-fecha_pago')

        headers = [
            'ID',
            'Pedido',
            'Empresa',
            'Monto Pagado',
            'Estado Pago',
            'Método de Pago',
            'Referencia',
            'Validado Por',
            'Fecha Pago',
            'Observaciones'
        ]

        datos = []
        total_pagado = 0
        for pago in pagos:
            datos.append([
                pago.id,
                pago.pedido.numero_orden,
                pago.pedido.empresa.nombre,
                f"${pago.monto:,.2f}",
                pago.get_estado_pago_display(),
                pago.get_metodo_pago_display(),
                pago.referencia_pago or 'N/A',
                pago.validado_por.nombre if pago.validado_por else 'Sin validar',
                pago.fecha_pago.strftime('%Y-%m-%d %H:%M'),
                pago.observaciones or ''
            ])
            if pago.estado_pago in [Pago.Estados.COMPLETADO, Pago.Estados.PARCIAL]:
                total_pagado += pago.monto

        datos.append([])
        datos.append(['', '', 'TOTAL PAGADO:', f"${total_pagado:,.2f}", '', '', '', '', '', ''])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Pagos', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator('Reporte de Pagos', headers, datos, orientacion='landscape')
        else:
            generator = ReporteExcelGenerator('Reporte_Pagos', headers, datos)

        return generator.generar()


class ReporteConsolidadoFinancieroAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos("reportes.exportar_pedidos", "reportes.exportar_facturacion", "reportes.exportar_pagos", "reportes.exportar_solicitudes")
    def get(self, request):
        periodo = request.query_params.get('periodo', 'mensual')
        formato = request.query_params.get('formato', 'excel')

        pedidos = Pedido.objects.filter(
            estado=True,
            estado_pedido=Pedido.Estados.COMPLETADO
        )

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pedidos = pedidos.filter(empresa=usuario.empresa)

        if periodo == 'mensual':
            trunc_func = TruncMonth
            formato_fecha = '%Y-%m'
        elif periodo == 'trimestral':
            trunc_func = TruncQuarter
            formato_fecha = '%Y-Q'
        else:
            trunc_func = TruncYear
            formato_fecha = '%Y'

        consolidado = pedidos.annotate(
            periodo_agrupado=trunc_func('fecha_completado')
        ).values('periodo_agrupado').annotate(
            total_pedidos=Count('id'),
            total_facturado=Sum('total')
        ).order_by('-periodo_agrupado')

        headers = ['Periodo', 'Total Pedidos', 'Total Facturado', 'Promedio por Pedido']

        datos = []
        gran_total = 0
        total_pedidos = 0

        for item in consolidado:
            periodo_str = item['periodo_agrupado'].strftime(formato_fecha)
            if periodo == 'trimestral':
                quarter = (item['periodo_agrupado'].month - 1) // 3 + 1
                periodo_str = f"{item['periodo_agrupado'].year}-Q{quarter}"

            promedio = item['total_facturado'] / item['total_pedidos'] if item['total_pedidos'] > 0 else 0

            datos.append([
                periodo_str,
                item['total_pedidos'],
                f"${item['total_facturado']:,.2f}",
                f"${promedio:,.2f}"
            ])

            gran_total += item['total_facturado']
            total_pedidos += item['total_pedidos']

        if total_pedidos > 0:
            datos.append([])
            datos.append([
                'TOTAL',
                total_pedidos,
                f"${gran_total:,.2f}",
                f"${gran_total / total_pedidos:,.2f}"
            ])

        titulo = f'Reporte Consolidado Financiero ({periodo.capitalize()})'

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Consolidado_Financiero', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator(titulo, headers, datos)
        else:
            generator = ReporteExcelGenerator('Reporte_Consolidado_Financiero', headers, datos)

        return generator.generar()
