from django.urls import path
from .views import (
    CategoriaListCreateAPIView, CategoriaDetailAPIView,
    ProductoListCreateAPIView, ProductoDetailAPIView,
    ProductoAlertasStockAPIView
)

urlpatterns = [
    path('api/categorias', CategoriaListCreateAPIView.as_view(), name='listar_crear_categorias'),
    path('api/categorias/<int:pk>', CategoriaDetailAPIView.as_view(), name='detalle_categoria'),
    path('api/productos', ProductoListCreateAPIView.as_view(), name='listar_crear_productos'),
    path('api/productos/<int:pk>', ProductoDetailAPIView.as_view(), name='detalle_producto'),
    path('api/productos/alertas_stock', ProductoAlertasStockAPIView.as_view(), name='alertas_stock'),
]
