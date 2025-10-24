from django.urls import path
from .views import (
    PedidoListAPIView,
    PedidoDetailAPIView,
    CrearPedidoDesdeSolicitudAPIView,
    ActualizarEstadoPedidoAPIView,
    EditarPedidoAPIView,
    DescargarFacturaPDFAPIView,
    ReenviarFacturaAPIView,
    AprobarPagoDiferidoAPIView,
    ListarPedidosPagoDiferidoAPIView
)

urlpatterns = [
    path('api/pedidos', PedidoListAPIView.as_view(), name='listarPedidos'),
    path('api/pedidos/<int:pk>', PedidoDetailAPIView.as_view(), name='detallePedido'),
    path('api/pedidos/crear', CrearPedidoDesdeSolicitudAPIView.as_view(), name='crearPedidoDesdeSolicitud'),
    path('api/pedidos/<int:pk>/estado', ActualizarEstadoPedidoAPIView.as_view(), name='actualizarEstadoPedido'),
    path('api/pedidos/<int:pk>/editar', EditarPedidoAPIView.as_view(), name='editarPedido'),
    path('api/pedidos/<int:pk>/factura', DescargarFacturaPDFAPIView.as_view(), name='descargarFacturaPDF'),
    path('api/pedidos/<int:pk>/reenviarFactura', ReenviarFacturaAPIView.as_view(), name='reenviarFactura'),
    path('api/pedidos/pago_diferido/pendientes', ListarPedidosPagoDiferidoAPIView.as_view(), name='listarPedidosPagoDiferidoPendientes'),
    path('api/pedidos/<int:pk>/aprobar_pago_diferido', AprobarPagoDiferidoAPIView.as_view(), name='aprobarPagoDiferido'),
]
