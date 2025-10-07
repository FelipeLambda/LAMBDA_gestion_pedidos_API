class FiltradoEmpresaMixin:

    def filtrar_por_empresa(self, request, queryset):
        """
        Filtra el queryset por empresa según el rol del usuario.
        """
        if request.user.is_superuser:
            return queryset

        if request.user.groups.filter(name='Admin Sistema').exists():
            return queryset

        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.user.empresa)

        return queryset


class PermisosPorEmpresaMixin:
    """Mixin para manejar permisos de visualización y eliminación por empresa"""

    def puede_ver_recurso(self, usuario, recurso, grupos_adicionales=None):
        """
        Verifica si un usuario puede ver un recurso basado en la empresa.

        Args:
            usuario: Usuario solicitante
            recurso: Objeto a verificar (debe tener atributos 'empresa' y 'solicitante')
            grupos_adicionales: Lista de grupos adicionales que pueden ver (ej: ['Validador Financiero'])

        Returns:
            tuple: (puede_ver: bool, mensaje_error: str)
        """
        if usuario.is_superuser:
            return True, None

        if usuario.groups.filter(name='Admin Sistema').exists():
            return True, None

        # Verificar grupos adicionales (ej: validadores) si se especifican
        if grupos_adicionales and usuario.groups.filter(name__in=grupos_adicionales).exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, f'No tiene permisos para ver recursos de otras empresas'

        # Admin Empresa
        if usuario.groups.filter(name='Admin Empresa').exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, f'No tiene permisos para ver recursos de otras empresas'

        # Solicitante propietario
        if hasattr(recurso, 'solicitante') and recurso.solicitante == usuario:
            return True, None

        return False, 'No tiene permisos para ver este recurso'

    def puede_eliminar_recurso(self, usuario, recurso):
        """
        Verifica si un usuario puede eliminar un recurso basado en la empresa.

        Args:
            usuario: Usuario solicitante
            recurso: Objeto a verificar (debe tener atributo 'empresa')

        Returns:
            tuple: (puede_eliminar: bool, mensaje_error: str)
        """
        if usuario.is_superuser or usuario.groups.filter(name='Admin Sistema').exists():
            return True, None

        if usuario.groups.filter(name='Admin Empresa').exists():
            if recurso.empresa == usuario.empresa:
                return True, None
            return False, 'No tiene permisos para eliminar recursos de otras empresas'

        return False, 'No tiene permisos para eliminar recursos'
