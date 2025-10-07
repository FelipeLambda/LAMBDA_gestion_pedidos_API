from django.urls import path
from .views import (
    MovimientoInventarioListAPIView,
    RegistrarMovimientoAPIView,
    StockProductoAPIView
)

urlpatterns = [
    path('api/inventario/movimientos', MovimientoInventarioListAPIView.as_view(), name='listarMovimientos'),
    path('api/inventario/movimientos/registrar', RegistrarMovimientoAPIView.as_view(), name='registrarMovimiento'),
    path('api/inventario/stock/<int:pk>', StockProductoAPIView.as_view(), name='consultarStock'),
]
