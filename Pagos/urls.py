from django.urls import path
from .views import (
    RegistrarPagoAPIView,
    ListarPagosAPIView,
    ValidarPagoAPIView,
    PagoDetailAPIView
)

urlpatterns = [
    path('api/pagos', ListarPagosAPIView.as_view(), name='listarPagos'),
    path('api/pagos/<int:pk>', PagoDetailAPIView.as_view(), name='detallePago'),
    path('api/pagos/registrar', RegistrarPagoAPIView.as_view(), name='registrarPago'),
    path('api/pagos/<int:pk>/validar', ValidarPagoAPIView.as_view(), name='validarPago'),
]
