import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Usuarios.models import Usuario
from Usuarios.serializers import UsuarioSerializer, RegistroUsuarioSerializer
from Usuarios.services import EmailService
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_grupos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    PermisosPorAreaMixin,
    manejar_errores_db
)
from Usuarios.models import Grupos


class UsuarioListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA, Grupos.JEFE_AREA)
    def get(self, request):
        usuarios = self.filtrar_por_empresa(request, Usuario.objects.all())

        if request.user.groups.filter(name=Grupos.JEFE_AREA).exists() and \
           not request.user.groups.filter(name=Grupos.ADMIN_EMPRESA).exists() and \
           not request.user.is_superuser:
            usuarios = usuarios.filter(area=request.user.area)

        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request):
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


class UsuarioDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, PermisosPorAreaMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA, Grupos.JEFE_AREA)
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

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

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


class AsignarGrupoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def post(self, request, pk):
        from django.contrib.auth.models import Group
        from Usuarios.serializers import AsignarGrupoSerializer
        from Usuarios.models_auditoria import RegistroAuditoriaGrupo

        usuario_target, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        serializer = AsignarGrupoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        grupo_nombre = serializer.validated_data['grupo']
        motivo = serializer.validated_data.get('motivo', '')

        if usuario_target.empresa != request.user.empresa and not request.user.is_superuser and not request.user.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes asignar grupos a usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if usuario_target == request.user and grupo_nombre == Grupos.ADMIN_EMPRESA:
            return Response(
                {'error': 'No puedes asignarte el grupo Admin Empresa a ti mismo. Otro Admin debe hacerlo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if usuario_target.groups.filter(name=grupo_nombre).exists():
            return Response(
                {'error': f'El usuario ya tiene el grupo {grupo_nombre}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grupo = Group.objects.get(name=grupo_nombre)
        usuario_target.groups.add(grupo)

        RegistroAuditoriaGrupo.objects.create(
            usuario_modificador=request.user,
            usuario_afectado=usuario_target,
            accion='ASIGNAR',
            grupo_nombre=grupo_nombre,
            empresa=usuario_target.empresa,
            motivo=motivo
        )

        return Response({
            'mensaje': f'Grupo {grupo_nombre} asignado exitosamente a {usuario_target.nombre}',
            'usuario': UsuarioSerializer(usuario_target).data
        }, status=status.HTTP_200_OK)


class RemoverGrupoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def post(self, request, pk):
        from django.contrib.auth.models import Group
        from Usuarios.serializers import RemoverGrupoSerializer
        from Usuarios.models_auditoria import RegistroAuditoriaGrupo

        usuario_target, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        serializer = RemoverGrupoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        grupo_nombre = serializer.validated_data['grupo']
        motivo = serializer.validated_data.get('motivo', '')

        if usuario_target.empresa != request.user.empresa and not request.user.is_superuser and not request.user.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes remover grupos de usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not usuario_target.groups.filter(name=grupo_nombre).exists():
            return Response(
                {'error': f'El usuario no tiene el grupo {grupo_nombre}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if grupo_nombre == Grupos.ADMIN_EMPRESA:
            admins_count = Usuario.objects.filter(
                empresa=usuario_target.empresa,
                groups__name=Grupos.ADMIN_EMPRESA,
                is_active=True,
                estado=True
            ).count()

            if admins_count <= 1:
                return Response(
                    {'error': 'No puedes remover el último Admin Empresa. Debe haber al menos un administrador.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        grupo = Group.objects.get(name=grupo_nombre)
        usuario_target.groups.remove(grupo)

        RegistroAuditoriaGrupo.objects.create(
            usuario_modificador=request.user,
            usuario_afectado=usuario_target,
            accion='REMOVER',
            grupo_nombre=grupo_nombre,
            empresa=usuario_target.empresa,
            motivo=motivo
        )

        return Response({
            'mensaje': f'Grupo {grupo_nombre} removido exitosamente de {usuario_target.nombre}',
            'usuario': UsuarioSerializer(usuario_target).data
        }, status=status.HTTP_200_OK)


class ListarGruposDisponiblesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        grupos_disponibles = [
            {
                'nombre': Grupos.ADMIN_EMPRESA,
                'descripcion': 'Administrador de la empresa con acceso completo a la gestión'
            },
            {
                'nombre': Grupos.JEFE_AREA,
                'descripcion': 'Gestiona usuarios y solicitudes únicamente de su área'
            },
            {
                'nombre': Grupos.VALIDADOR_FINANCIERO,
                'descripcion': 'Valida y aprueba solicitudes desde perspectiva financiera'
            },
            {
                'nombre': Grupos.VALIDADOR_ABASTECIMIENTO,
                'descripcion': 'Valida y aprueba solicitudes desde perspectiva de stock/logística'
            },
            {
                'nombre': Grupos.SOLICITANTE,
                'descripcion': 'Usuario base que puede crear solicitudes de productos'
            }
        ]

        return Response({
            'grupos': grupos_disponibles,
            'nota': 'El grupo Admin Sistema solo puede ser asignado por LAMBDA'
        }, status=status.HTTP_200_OK)
