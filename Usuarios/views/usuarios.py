import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Usuarios.models import Usuario, Grupos
from Usuarios.serializers import (
    UsuarioSerializer,
    RegistroUsuarioSerializer
)
from Usuarios.services import EmailService
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_permisos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    PermisosPorAreaMixin,
    manejar_errores_db
)


class UsuarioListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('usuarios.listar')
    def get(self, request):
        usuarios = self.filtrar_por_empresa(request, Usuario.objects.all())

        if request.user.roles.filter(nombre=Grupos.JEFE_AREA).exists() and \
           not request.user.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists() and \
           not request.user.is_superuser:
            usuarios = usuarios.filter(area=request.user.area)

        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('usuarios.crear')
    def post(self, request):
        empresa_id = request.data.get('empresa')

        if not self._puede_crear_usuario_para_empresa(request.user, empresa_id):
            return Response(
                {'error': 'No tiene permisos para crear usuarios para esta empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RegistroUsuarioSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        usuario = serializer.save()

        token = secrets.token_urlsafe(32)
        usuario.token_activacion = token
        usuario.token_expiracion = timezone.now() + timedelta(days=7)
        usuario.is_active = False
        usuario.save()

        EmailService.enviar_email_activacion(usuario, token)

        return Response({
            'mensaje': 'Usuario creado exitosamente. Se ha enviado un correo de activación.',
            'usuario': UsuarioSerializer(usuario).data
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def _puede_crear_usuario_para_empresa(usuario, empresa_id):
        if usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return True

        if usuario.empresa and usuario.empresa.id == empresa_id:
            return True

        return False


class UsuarioDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, PermisosPorAreaMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        if not self._puede_ver_usuario(request.user, usuario):
            return Response(
                {'error': 'No tiene permisos para ver este usuario'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _puede_ver_usuario(self, usuario_logueado, usuario_target):
        if usuario_logueado.is_superuser or usuario_logueado.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return True

        if usuario_logueado.id == usuario_target.id:
            return True

        if not usuario_logueado.empresa or not usuario_target.empresa:
            return False

        if usuario_logueado.empresa.id != usuario_target.empresa.id:
            return False

        if usuario_logueado.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
            return True

        if usuario_logueado.roles.filter(nombre=Grupos.JEFE_AREA).exists():
            if usuario_logueado.area and usuario_target.area:
                return usuario_logueado.area.id == usuario_target.area.id
            return False

        return False

    @requiere_permisos('usuarios.editar')
    @manejar_errores_db
    def put(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        puede, mensaje = self.puede_gestionar_en_area(request.user, usuario)
        if not puede:
            return Response({'error': mensaje}, status=status.HTTP_403_FORBIDDEN)

        serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Usuario actualizado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

class RegenerarTokenUsuarioAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('usuarios.regenerar_token')
    def post(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        if usuario.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes regenerar tokens de usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if usuario.is_active:
            return Response(
                {'error': 'El usuario ya está activo. No se puede regenerar el token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = secrets.token_urlsafe(32)
        usuario.token_activacion = token
        usuario.token_expiracion = timezone.now() + timedelta(days=7)
        usuario.save()

        EmailService.enviar_email_activacion(usuario, token)

        return Response({
            'mensaje': 'Token regenerado exitosamente. Se ha enviado un nuevo correo de activación.',
            'token_expiracion': usuario.token_expiracion
        }, status=status.HTTP_200_OK)


class ActivarDesactivarUsuarioAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('usuarios.activar_desactivar')
    @manejar_errores_db
    def post(self, request, pk):
        usuario_target, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        accion = request.data.get('accion')

        if not accion or accion not in ['activar', 'inactivar']:
            return Response(
                {'error': 'Debe especificar una acción válida: "activar" o "inactivar"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if usuario_target.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes gestionar usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if usuario_target == request.user:
            return Response(
                {'error': 'No puedes cambiar tu propio estado de activación'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if accion == 'activar':
            if usuario_target.is_active:
                return Response(
                    {'error': 'El usuario ya está activo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            usuario_target.is_active = True
            mensaje = f'Usuario {usuario_target.nombre} activado exitosamente'
        else:
            if not usuario_target.is_active:
                return Response(
                    {'error': 'El usuario ya está inactivo'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if usuario_target.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
                admins_count = Usuario.objects.filter(
                    empresa=usuario_target.empresa,
                    roles__nombre=Grupos.ADMIN_EMPRESA,
                    is_active=True,
                    estado=True
                ).count()

                if admins_count <= 1:
                    return Response(
                        {'error': 'No puedes desactivar el último Admin Empresa activo. Debe haber al menos un administrador.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            usuario_target.is_active = False
            mensaje = f'Usuario {usuario_target.nombre} desactivado exitosamente'

        usuario_target.save()

        return Response({
            'mensaje': mensaje,
            'usuario': UsuarioSerializer(usuario_target).data
        }, status=status.HTTP_200_OK)
