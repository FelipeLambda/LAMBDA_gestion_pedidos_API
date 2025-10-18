from rest_framework import status
from rest_framework.response import Response
from Usuarios.models import Grupos


class FiltradoEmpresaMixin:
    def filtrar_por_empresa(self, request, queryset):
        if self._es_admin_global(request.user):
            return queryset

        if not request.user.empresa:
            return queryset.none()

        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.user.empresa)

        return queryset

    @staticmethod
    def _es_admin_global(usuario):
        return usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists()


class PermisosPorEmpresaMixin:
    def puede_ver_recurso(self, usuario, recurso, roles_adicionales=None):
        if self._es_admin_global(usuario):
            return True, None

        es_valido, mensaje = self._validar_empresa_usuario(usuario)
        if not es_valido:
            return False, mensaje

        if roles_adicionales and usuario.roles.filter(nombre__in=roles_adicionales).exists():
            return self._verificar_misma_empresa(usuario, recurso)

        if usuario.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
            return self._verificar_misma_empresa(usuario, recurso)

        if hasattr(recurso, 'solicitante') and recurso.solicitante == usuario:
            return True, None

        return False, 'No tiene permisos para ver este recurso'

    def puede_eliminar_recurso(self, usuario, recurso):
        if self._es_admin_global(usuario):
            return True, None

        es_valido, mensaje = self._validar_empresa_usuario(usuario)
        if not es_valido:
            return False, mensaje

        if usuario.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
            return self._verificar_misma_empresa(usuario, recurso, 'eliminar')

        return False, 'No tiene permisos para eliminar recursos'

    @staticmethod
    def _es_admin_global(usuario):
        return usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists()

    @staticmethod
    def _validar_empresa_usuario(usuario):
        if not usuario.empresa:
            return False, 'Usuario sin empresa asignada. Contacte al administrador.'
        return True, None

    @staticmethod
    def _verificar_misma_empresa(usuario, recurso, accion='ver'):
        if recurso.empresa == usuario.empresa:
            return True, None
        return False, f'No tiene permisos para {accion} recursos de otras empresas'


class PermisosPorAreaMixin:
    def puede_gestionar_en_area(self, usuario, recurso):
        if self._es_admin_global(usuario):
            return True, None

        es_valido, mensaje = self._validar_empresa_usuario(usuario)
        if not es_valido:
            return False, mensaje

        if usuario.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
            return self._verificar_misma_empresa(usuario, recurso)

        if usuario.roles.filter(nombre=Grupos.JEFE_AREA).exists():
            if not usuario.area:
                return False, 'Jefe de Área sin área asignada'

            if hasattr(recurso, 'area') and recurso.area == usuario.area:
                return True, None
            elif hasattr(recurso, 'solicitante') and recurso.solicitante.area == usuario.area:
                return True, None

            return False, 'Solo puede gestionar recursos de su área'

        return False, 'No tiene permisos para gestionar recursos'

    @staticmethod
    def _es_admin_global(usuario):
        return usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists()

    @staticmethod
    def _validar_empresa_usuario(usuario):
        if not usuario.empresa:
            return False, 'Usuario sin empresa asignada. Contacte al administrador.'
        return True, None

    @staticmethod
    def _verificar_misma_empresa(usuario, recurso, accion='gestionar'):
        if recurso.empresa == usuario.empresa:
            return True, None
        return False, f'No tiene permisos para {accion} recursos de otras empresas'


class ObjetoDetailMixin:
    @staticmethod
    def obtener_objeto_o_404(modelo, pk, mensaje_error=None, usar_soft_delete=True):
        try:
            if usar_soft_delete and hasattr(modelo, 'estado'):
                objeto = modelo.objects.get(pk=pk, estado=True)
            else:
                objeto = modelo.objects.get(pk=pk)
            return objeto, None
        except modelo.DoesNotExist:
            if not mensaje_error:
                nombre_modelo = modelo.__name__
                mensaje_error = f'{nombre_modelo} no encontrado'
            return None, Response(
                {'error': mensaje_error},
                status=status.HTTP_404_NOT_FOUND
            )


class SerializerValidationMixin:
    @staticmethod
    def validar_serializer(serializer):
        if not serializer.is_valid():
            return False, Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return True, None
