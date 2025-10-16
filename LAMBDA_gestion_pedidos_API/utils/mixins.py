from rest_framework import status
from rest_framework.response import Response
from Usuarios.models import Grupos, Permiso

def obtener_permisos_de_usuario(usuario):
    if usuario.is_superuser:
        return set(Permiso.objects.values_list('codigo', flat=True))

    permisos = set()
    for rol in usuario.roles.all():
        permisos.update(rol.permisos.values_list('codigo', flat=True))

    return permisos

def verificar_permiso_usuario(usuario, codigo_permiso):
    if usuario.is_superuser:
        return True

    permisos_usuario = obtener_permisos_de_usuario(usuario)
    return codigo_permiso in permisos_usuario

def verificar_alguno_de_permisos(usuario, codigos_permisos):
    if usuario.is_superuser:
        return True

    permisos_usuario = obtener_permisos_de_usuario(usuario)
    return any(codigo in permisos_usuario for codigo in codigos_permisos)

def verificar_todos_permisos(usuario, codigos_permisos):
    if usuario.is_superuser:
        return True

    permisos_usuario = obtener_permisos_de_usuario(usuario)
    return all(codigo in permisos_usuario for codigo in codigos_permisos)

class FiltradoEmpresaMixin:
    """Mixin para filtrar recursos por empresa del usuario"""

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
        return usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists()

class PermisosPorEmpresaMixin:
    """Mixin para validar permisos de acceso a recursos por empresa"""

    def puede_ver_recurso(self, usuario, recurso, grupos_adicionales=None):
        if self._es_admin_global(usuario):
            return True, None

        es_valido, mensaje = self._validar_empresa_usuario(usuario)
        if not es_valido:
            return False, mensaje

        if grupos_adicionales and usuario.groups.filter(name__in=grupos_adicionales).exists():
            return self._verificar_misma_empresa(usuario, recurso)

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
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

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            return self._verificar_misma_empresa(usuario, recurso, 'eliminar')

        return False, 'No tiene permisos para eliminar recursos'

    @staticmethod
    def _es_admin_global(usuario):
        return usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists()

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


class ObjetoDetailMixin:
    """Mixin para obtener objetos con manejo automático de 404"""

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
    """Mixin para validar serializers con manejo automático de errores"""

    @staticmethod
    def validar_serializer(serializer):
        if not serializer.is_valid():
            return False, Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return True, None


class PermisosPorAreaMixin:
    """Mixin para validar permisos limitados por área"""

    def puede_gestionar_en_area(self, usuario, recurso):
        if self._es_admin_global(usuario):
            return True, None

        es_valido, mensaje = self._validar_empresa_usuario(usuario)
        if not es_valido:
            return False, mensaje

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            return self._verificar_misma_empresa(usuario, recurso)

        if usuario.groups.filter(name=Grupos.JEFE_AREA).exists():
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
        return usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists()

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

class PermisosRBACMixin:
    """Mixin para verificar permisos RBAC granulares en vistas."""

    def usuario_tiene_permiso(self, usuario, codigo_permiso):
        return verificar_permiso_usuario(usuario, codigo_permiso)

    def usuario_tiene_alguno_de(self, usuario, codigos_permisos):
        return verificar_alguno_de_permisos(usuario, codigos_permisos)

    def usuario_tiene_todos(self, usuario, codigos_permisos):
        return verificar_todos_permisos(usuario, codigos_permisos)

    def obtener_permisos_usuario(self, usuario):
        return obtener_permisos_de_usuario(usuario)

    def validar_permiso_o_403(self, usuario, codigo_permiso, mensaje_error=None):
        if self.usuario_tiene_permiso(usuario, codigo_permiso):
            return True, None

        if not mensaje_error:
            mensaje_error = f'No tienes el permiso necesario: {codigo_permiso}'

        return False, Response(
            {'error': mensaje_error},
            status=status.HTTP_403_FORBIDDEN
        )
