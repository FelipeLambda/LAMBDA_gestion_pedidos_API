class FiltradoEmpresaMixin:

    def filtrar_por_empresa(self, request, queryset):
        """
        Filtra el queryset por empresa si el usuario NO es Admin Sistema.
        """
        if request.user.groups.filter(name='Admin Sistema').exists():
            return queryset

        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.user.empresa)

        return queryset
