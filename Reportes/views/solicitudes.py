from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Solicitudes.models import Solicitud
from Reportes.serializers import FiltroReporteSolicitudesSerializer
from Reportes.utils import ReporteExcelGenerator, ReporteCSVGenerator
from Reportes.utils_pdf import ReportePDFGenerator
from LAMBDA_gestion_pedidos_API.utils import requiere_grupos
from Usuarios.models import Grupos


class ExportarSolicitudesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        serializer = FiltroReporteSolicitudesSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filtros = serializer.validated_data
        formato = filtros.pop('formato', 'excel')

        solicitudes = Solicitud.objects.select_related(
            'empresa', 'area', 'solicitante',
            'validador_financiero', 'validador_abastecimiento'
        ).prefetch_related('detalles__producto')

        usuario = request.user
        if not usuario.is_superuser and not usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            solicitudes = solicitudes.filter(empresa=usuario.empresa)

        if filtros.get('empresa_id'):
            solicitudes = solicitudes.filter(empresa_id=filtros['empresa_id'])

        if filtros.get('fecha_desde'):
            solicitudes = solicitudes.filter(fecha_creacion__gte=filtros['fecha_desde'])

        if filtros.get('fecha_hasta'):
            solicitudes = solicitudes.filter(fecha_creacion__lte=filtros['fecha_hasta'])

        if filtros.get('estado'):
            solicitudes = solicitudes.filter(estado_solicitud=filtros['estado'])

        if filtros.get('solicitante_id'):
            solicitudes = solicitudes.filter(solicitante_id=filtros['solicitante_id'])

        solicitudes = solicitudes.filter(estado=True)

        headers = [
            'ID',
            'Empresa',
            'Área',
            'Solicitante',
            'Email Solicitante',
            'Estado',
            'Total',
            'Cantidad Items',
            'Validador Abastecimiento',
            'Fecha Validación Abastecimiento',
            'Validador Financiero',
            'Fecha Validación Financiero',
            'Observaciones',
            'Fecha Creación',
        ]

        datos = []
        for sol in solicitudes:
            datos.append([
                sol.id,
                sol.empresa.nombre,
                sol.area.nombre if sol.area else 'N/A',
                sol.solicitante.nombre,
                sol.solicitante.email,
                sol.get_estado_solicitud_display(),
                f"{sol.total:.2f}",
                sol.cantidad_items,
                sol.validador_abastecimiento.nombre if sol.validador_abastecimiento else 'N/A',
                sol.fecha_validacion_abastecimiento.strftime('%Y-%m-%d %H:%M') if sol.fecha_validacion_abastecimiento else 'N/A',
                sol.validador_financiero.nombre if sol.validador_financiero else 'N/A',
                sol.fecha_validacion_financiero.strftime('%Y-%m-%d %H:%M') if sol.fecha_validacion_financiero else 'N/A',
                sol.observaciones or '',
                sol.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
            ])

        if formato == 'csv':
            generator = ReporteCSVGenerator('Reporte_Solicitudes', headers, datos)
        elif formato == 'pdf':
            generator = ReportePDFGenerator('Reporte de Solicitudes', headers, datos, orientacion='landscape')
        else:
            generator = ReporteExcelGenerator('Reporte_Solicitudes', headers, datos)

        return generator.generar()
