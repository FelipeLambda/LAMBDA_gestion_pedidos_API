class FiltradoEmpresaMixin:

    def filtrar_por_empresa(self, request, queryset):
        """
        Filtra el queryset por empresa según el rol del usuario.
        - Superusuarios (is_superuser=True): ven todo sin restricciones
        - Admin Sistema: ven todo
        - Otros: solo ven datos de su empresa
        """
        if request.user.is_superuser:
            return queryset

        if request.user.groups.filter(name='Admin Sistema').exists():
            return queryset

        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.user.empresa)

        return queryset
