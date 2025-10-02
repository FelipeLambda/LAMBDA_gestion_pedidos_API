from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def requiere_admin_sistema(vista_metodo):
    """
    Decorador para verificar si el usuario es administrador del sistema.

    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Debe estar autenticado para realizar esta acción.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.es_admin_sistema:
            return Response(
                {'error': 'Solo los administradores del sistema pueden realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vista_metodo(self, request, *args, **kwargs)
    return wrapper


def requiere_admin_empresa(vista_metodo):
    """
    Decorador para verificar si el usuario es administrador de empresa.

    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Debe estar autenticado para realizar esta acción.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.es_admin_empresa and not request.user.es_admin_sistema:
            return Response(
                {'error': 'Solo los administradores de empresa pueden realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vista_metodo(self, request, *args, **kwargs)
    return wrapper


def requiere_validador_financiero(vista_metodo):
    """
    Decorador para verificar si el usuario es validador financiero.

    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Debe estar autenticado para realizar esta acción.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.es_validador_financiero:
            return Response(
                {'error': 'Solo los validadores financieros pueden realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vista_metodo(self, request, *args, **kwargs)
    return wrapper


def requiere_validador_abastecimiento(vista_metodo):
    """
    Decorador para verificar si el usuario es validador de abastecimiento.

    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Debe estar autenticado para realizar esta acción.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.es_validador_abastecimiento:
            return Response(
                {'error': 'Solo los validadores de abastecimiento pueden realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vista_metodo(self, request, *args, **kwargs)
    return wrapper


def requiere_solicitante(vista_metodo):
    """
    Decorador para verificar si el usuario puede crear solicitudes.

    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Debe estar autenticado para realizar esta acción.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.es_solicitante:
            return Response(
                {'error': 'Solo los usuarios con permisos de solicitante pueden realizar esta acción.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return vista_metodo(self, request, *args, **kwargs)
    return wrapper


def requiere_permiso(permiso_codename):
    """
    Decorador genérico para verificar permisos personalizados de Django.

    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'error': 'Debe estar autenticado para realizar esta acción.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not request.user.has_perm(permiso_codename):
                return Response(
                    {'error': f'No tiene el permiso necesario: {permiso_codename}'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return vista_metodo(self, request, *args, **kwargs)
        return wrapper
    return decorador


# Funciones auxiliares para verificar permisos sin decorador 
def verificar_admin_sistema(usuario):
    """
    Verifica si el usuario es admin del sistema.
    Retorna (True/False, mensaje_error)
    """
    if not usuario or not usuario.is_authenticated:
        return False, 'Debe estar autenticado para realizar esta acción.'

    if not usuario.es_admin_sistema:
        return False, 'Solo los administradores del sistema pueden realizar esta acción.'

    return True, None


def verificar_admin_empresa(usuario):
    """
    Verifica si el usuario es admin de empresa.
    Retorna (True/False, mensaje_error)
    """
    if not usuario or not usuario.is_authenticated:
        return False, 'Debe estar autenticado para realizar esta acción.'

    if not usuario.es_admin_empresa and not usuario.es_admin_sistema:
        return False, 'Solo los administradores de empresa pueden realizar esta acción.'

    return True, None


def verificar_permiso(usuario, permiso_codename):
    """
    Verifica si el usuario tiene un permiso específico.
    Retorna (True/False, mensaje_error)
    """
    if not usuario or not usuario.is_authenticated:
        return False, 'Debe estar autenticado para realizar esta acción.'

    if not usuario.has_perm(permiso_codename):
        return False, f'No tiene el permiso necesario: {permiso_codename}'

    return True, None
