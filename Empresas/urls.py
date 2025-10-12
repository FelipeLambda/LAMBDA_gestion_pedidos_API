from django.urls import path
from .views import (
    EmpresaListCreateAPIView, EmpresaDetailAPIView,
    AreaListCreateAPIView, AreaDetailAPIView,
    ActivarEmpresaAPIView, RegenerarTokenEmpresaAPIView
)

urlpatterns = [
    path('api/empresas', EmpresaListCreateAPIView.as_view(), name='listarCrearEmpresas'),
    path('api/empresas/<int:pk>', EmpresaDetailAPIView.as_view(), name='detalleEmpresa'),
    path('api/empresas/<int:pk>/regenerar-token', RegenerarTokenEmpresaAPIView.as_view(), name='regenerarTokenEmpresa'),
    path('api/empresas/activar', ActivarEmpresaAPIView.as_view(), name='activarEmpresa'),
    path('api/areas', AreaListCreateAPIView.as_view(), name='listarCrearAreas'),
    path('api/areas/<int:pk>', AreaDetailAPIView.as_view(), name='detalleArea'),
]
