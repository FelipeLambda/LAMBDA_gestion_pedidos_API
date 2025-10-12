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
    manejar_errores_db
)
from Usuarios.models import Grupos


class UsuarioListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        usuarios = self.filtrar_por_empresa(request, Usuario.objects.all())
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


class UsuarioDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        usuario, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

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
