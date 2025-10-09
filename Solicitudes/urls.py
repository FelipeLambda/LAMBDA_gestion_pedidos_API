from django.urls import path
from .views import (
    SolicitudListCreateAPIView,
    SolicitudDetailAPIView,
    ValidarSolicitudFinancieroAPIView,
    ValidarSolicitudAbastecimientoAPIView
)

urlpatterns = [
    path('api/solicitudes', SolicitudListCreateAPIView.as_view(), name='listarCrearSolicitudes'),
    path('api/solicitudes/<int:pk>', SolicitudDetailAPIView.as_view(), name='detalleSolicitud'),
    path('api/solicitudes/<int:pk>/validarFinanciero', ValidarSolicitudFinancieroAPIView.as_view(), name='validarSolicitudFinanciero'),
    path('api/solicitudes/<int:pk>/validarAbastecimiento', ValidarSolicitudAbastecimientoAPIView.as_view(), name='validarSolicitudAbastecimiento'),
]
