from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Empresa, Area, Usuario

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'sector', 'pagar_despues', 'estado', 'created_at']
    list_filter = ['pagar_despues', 'estado', 'sector']
    search_fields = ['nombre', 'nit', 'correo_contacto']
    ordering = ['nombre']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'estado', 'created_at']
    list_filter = ['estado', 'empresa']
    search_fields = ['nombre', 'empresa__nombre']
    ordering = ['empresa', 'nombre']


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['email', 'nombre', 'empresa', 'cargo', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'es_admin_sistema', 'es_admin_empresa', 'empresa']
    search_fields = ['email', 'nombre', 'cargo']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'cargo')}),
        ('Empresa y área', {'fields': ('empresa', 'area')}),
        ('Roles', {'fields': ('es_admin_sistema', 'es_admin_empresa', 'es_validador_financiero', 'es_validador_abastecimiento', 'es_solicitante')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'empresa', 'area', 'cargo'),
        }),
    )
