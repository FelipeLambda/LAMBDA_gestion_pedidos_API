from django.contrib import admin
from .models import Categoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado', 'created_at']
    list_filter = ['estado']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['sku', 'nombre', 'categoria', 'precio', 'stock_disponible', 'umbral_minimo', 'estado', 'created_at']
    list_filter = ['estado', 'categoria']
    search_fields = ['nombre', 'sku', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion', 'sku', 'categoria')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock_disponible', 'umbral_minimo')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Personaliza el queryset para optimizar consultas.
        """
        qs = super().get_queryset(request)
        return qs.select_related('categoria')
