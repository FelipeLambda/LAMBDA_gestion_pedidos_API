from django.urls import path
from .views import (
    ExportarSolicitudesAPIView,
    ExportarPedidosAPIView,
    ExportarInventarioAPIView,
    ExportarStockProductosAPIView,
    ReporteFacturacionAPIView,
    ReportePagosAPIView,
    ReporteConsolidadoFinancieroAPIView
)

urlpatterns = [
    path('api/reportes/solicitudes/exportar', ExportarSolicitudesAPIView.as_view(), name='exportarSolicitudes'),
    path('api/reportes/pedidos/exportar', ExportarPedidosAPIView.as_view(), name='exportarPedidos'),
    path('api/reportes/inventario/exportar', ExportarInventarioAPIView.as_view(), name='exportarInventario'),
    path('api/reportes/stock/exportar', ExportarStockProductosAPIView.as_view(), name='exportarStock'),
    path('api/reportes/facturacion', ReporteFacturacionAPIView.as_view(), name='reporteFacturacion'),
    path('api/reportes/pagos', ReportePagosAPIView.as_view(), name='reportePagos'),
    path('api/reportes/consolidadoFinanciero', ReporteConsolidadoFinancieroAPIView.as_view(), name='reporteConsolidadoFinanciero'),
]
