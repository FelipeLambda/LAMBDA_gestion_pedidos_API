from Usuarios.models import Grupos


class FiltradoEmpresaMixin:

    def filtrar_por_empresa(self, request, queryset):
        if request.user.is_superuser:
            return queryset

        if request.user.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return queryset

        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.user.empresa)

        return queryset


class PermisosPorEmpresaMixin:

    def puede_ver_recurso(self, usuario, recurso, grupos_adicionales=None):
        if usuario.is_superuser:
            return True, None

        if usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return True, None

        if grupos_adicionales and usuario.groups.filter(name__in=grupos_adicionales).exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, 'No tiene permisos para ver recursos de otras empresas'

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, 'No tiene permisos para ver recursos de otras empresas'

        if hasattr(recurso, 'solicitante') and recurso.solicitante == usuario:
            return True, None

        return False, 'No tiene permisos para ver este recurso'

    def puede_eliminar_recurso(self, usuario, recurso):
        if usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return True, None

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, 'No tiene permisos para eliminar recursos de otras empresas'

        return False, 'No tiene permisos para eliminar recursos'
