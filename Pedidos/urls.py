from django.urls import path
from .views import (
    PedidoListAPIView,
    PedidoDetailAPIView,
    CrearPedidoDesdeSolicitudAPIView,
    ActualizarEstadoPedidoAPIView,
    EditarPedidoAPIView
)

urlpatterns = [
    path('api/pedidos', PedidoListAPIView.as_view(), name='listarPedidos'),
    path('api/pedidos/<int:pk>', PedidoDetailAPIView.as_view(), name='detallePedido'),
    path('api/pedidos/crear', CrearPedidoDesdeSolicitudAPIView.as_view(), name='crearPedidoDesdeSolicitud'),
    path('api/pedidos/<int:pk>/estado', ActualizarEstadoPedidoAPIView.as_view(), name='actualizarEstadoPedido'),
    path('api/pedidos/<int:pk>/editar', EditarPedidoAPIView.as_view(), name='editarPedido'),
]
