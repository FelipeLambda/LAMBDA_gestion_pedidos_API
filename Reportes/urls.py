from django.urls import path
from .views import (
    ExportarSolicitudesAPIView,
    ExportarPedidosAPIView,
    ExportarInventarioAPIView,
    ExportarStockProductosAPIView
)

urlpatterns = [
    path('api/reportes/solicitudes/exportar', ExportarSolicitudesAPIView.as_view(), name='exportarSolicitudes'),
    path('api/reportes/pedidos/exportar', ExportarPedidosAPIView.as_view(), name='exportarPedidos'),
    path('api/reportes/inventario/exportar', ExportarInventarioAPIView.as_view(), name='exportarInventario'),
    path('api/reportes/stock/exportar', ExportarStockProductosAPIView.as_view(), name='exportarStock'),
]
