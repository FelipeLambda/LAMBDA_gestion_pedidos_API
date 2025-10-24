import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

logger = logging.getLogger(__name__)


def requiere_permisos(*codigos_permisos):
    def decorador(vista_metodo):
        @wraps(vista_metodo)
        def wrapper(self, request, *args, **kwargs):
            usuario = request.user

            if usuario.is_superuser:
                return vista_metodo(self, request, *args, **kwargs)

            if usuario.roles.filter(permisos__codigo__in=codigos_permisos).exists():
                return vista_metodo(self, request, *args, **kwargs)

            permisos_str = ' o '.join(codigos_permisos)
            return Response(
                {'error': f'No tienes los permisos necesarios. Se requiere: {permisos_str}'},
                status=status.HTTP_403_FORBIDDEN
            )
        return wrapper
    return decorador


def manejar_errores_db(vista_metodo):
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
