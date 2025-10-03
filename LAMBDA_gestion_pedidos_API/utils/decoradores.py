from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
import logging

logger = logging.getLogger(__name__)


def requiere_grupos(*nombres_grupos):
    """
    Decorador genérico para verificar membresía a grupos de Django.
    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.groups.filter(name__in=nombres_grupos).exists():
                grupos_str = ', '.join(nombres_grupos)
                return Response(
                    {'error': f'Solo los usuarios de los grupos {grupos_str} pueden realizar esta acción.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return vista_metodo(self, request, *args, **kwargs)
        return wrapper
    return decorador


def requiere_permiso(permiso_codename):
    """
    Decorador para verificar permisos personalizados de Django.
    """
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
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

def requiere_admin_sistema(vista_metodo):
    """
    Decorador para verificar si el usuario es administrador del sistema.
    """
    return requiere_grupos('Admin Sistema')(vista_metodo)

def requiere_admin_empresa(vista_metodo):
    """
    Decorador para verificar si el usuario es administrador de empresa.
    """
    return requiere_grupos('Admin Empresa', 'Admin Sistema')(vista_metodo)


def requiere_validador_financiero(vista_metodo):
    """
    Decorador para verificar si el usuario es validador financiero.
    """
    return requiere_grupos('Validador Financiero')(vista_metodo)


def requiere_validador_abastecimiento(vista_metodo):
    """
    Decorador para verificar si el usuario es validador de abastecimiento.
    """
    return requiere_grupos('Validador Abastecimiento')(vista_metodo)


def requiere_solicitante(vista_metodo):
    """
    Decorador para verificar si el usuario puede crear solicitudes.
    """
    return requiere_grupos('Solicitante')(vista_metodo)

