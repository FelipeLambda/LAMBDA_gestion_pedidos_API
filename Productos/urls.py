from django.urls import path
from .views import (
    CategoriaListCreateAPIView, CategoriaDetailAPIView,
    ProductoListCreateAPIView, ProductoDetailAPIView,
    ProductoAlertasStockAPIView
)

urlpatterns = [
    path('api/categorias', CategoriaListCreateAPIView.as_view(), name='listarCrearCategorias'),
    path('api/categorias/<int:pk>', CategoriaDetailAPIView.as_view(), name='detalleCategoria'),
    path('api/productos', ProductoListCreateAPIView.as_view(), name='listarCrearProductos'),
    path('api/productos/<int:pk>', ProductoDetailAPIView.as_view(), name='detalleProducto'),
    path('api/productos/alertas_stock', ProductoAlertasStockAPIView.as_view(), name='alertasStock'),
]
