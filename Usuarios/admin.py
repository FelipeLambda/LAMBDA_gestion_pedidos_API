from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Permiso, Role


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['email', 'nombre', 'empresa', 'cargo', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'groups', 'empresa']
    search_fields = ['email', 'nombre', 'cargo']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'cargo')}),
        ('Empresa y área', {'fields': ('empresa', 'area')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'empresa', 'area', 'cargo'),
        }),
    )


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'modulo']
    list_filter = ['modulo']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['modulo', 'codigo']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'empresa', 'es_modificable', 'fecha_creacion']
    list_filter = ['tipo', 'es_modificable', 'empresa']
    search_fields = ['nombre', 'descripcion']
    filter_horizontal = ['permisos']
    ordering = ['tipo', 'nombre']

    fieldsets = (
        (None, {'fields': ('nombre', 'descripcion')}),
        ('Clasificación', {'fields': ('tipo', 'empresa', 'es_modificable')}),
        ('Permisos', {'fields': ('permisos',)}),
        ('Auditoría', {'fields': ('creado_por',)}),
    )
