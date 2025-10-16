import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from .mixins import verificar_alguno_de_permisos

logger = logging.getLogger(__name__)


def requiere_grupos(*nombres_grupos):
    """
    Decorador genérico para verificar membresía a grupos de Django.
    Los superusuarios (is_superuser=True) siempre tienen acceso.
    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            if request.user.is_superuser:
                return vista_metodo(self, request, *args, **kwargs)

            if not request.user.groups.filter(name__in=nombres_grupos).exists():
                grupos_str = ', '.join(nombres_grupos)
                return Response(
                    {'error': f'Solo los usuarios de los grupos {grupos_str} pueden realizar esta acción.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return vista_metodo(self, request, *args, **kwargs)
        return wrapper
    return decorador

def requiere_permisos(*codigos_permisos):
    """
    Decorador para verificar permisos RBAC granulares.
    Verifica que el usuario tenga AL MENOS UNO de los permisos especificados.
    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            if verificar_alguno_de_permisos(request.user, codigos_permisos):
                return vista_metodo(self, request, *args, **kwargs)

            permisos_str = ' o '.join(codigos_permisos)
            return Response(
                {'error': f'No tienes los permisos necesarios. Se requiere: {permisos_str}'},
                status=status.HTTP_403_FORBIDDEN
            )

        return wrapper
    return decorador


def requiere_permiso(permiso_codename):
    """
    Decorador para verificar permisos personalizados de Django.
    Los superusuarios (is_superuser=True) siempre tienen acceso.
    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            if request.user.is_superuser:
                return vista_metodo(self, request, *args, **kwargs)

            if not request.user.has_perm(permiso_codename):
                return Response(
                    {'error': f'No tiene el permiso necesario: {permiso_codename}'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return vista_metodo(self, request, *args, **kwargs)
        return wrapper
    return decorador


def manejar_errores_db(vista_metodo):
    """
    Decorador para manejo robusto de errores de base de datos y excepciones genéricas.
    """
    @wraps(vista_metodo)
    def wrapper(self, request, *args, **kwargs):
        try:
            return vista_metodo(self, request, *args, **kwargs)

        except ObjectDoesNotExist:
            raise

        except DatabaseError:
            logger.error(f"Error de BD en {vista_metodo.__name__}")
            return Response(
                {'error': 'Error de conexión con la base de datos. Intente más tarde.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as e:
            logger.error(f"Error en {vista_metodo.__name__}: {str(e)}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper

