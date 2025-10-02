import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from Usuarios.models import Usuario
from Usuarios.serializers import UsuarioSerializer, RegistroUsuarioSerializer
from LAMBDA_gestion_pedidos_API.utils import requiere_admin_empresa


class UsuarioListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Solo admin sistema o admin empresa pueden ver usuarios
        if not (request.user.es_admin_sistema or request.user.es_admin_empresa):
            return Response(
                {'error': 'No tiene permisos para ver usuarios.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.user.es_admin_sistema:
            usuarios = Usuario.objects.all()
        else:
            usuarios = Usuario.objects.filter(empresa=request.user.empresa)
        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_admin_empresa
    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()

            # Generar token de activación
            token = secrets.token_urlsafe(32)
            usuario.token_activacion = token
            usuario.token_expiracion = timezone.now() + timedelta(days=7)
            usuario.is_active = False
            usuario.save()

            # Enviar email de bienvenida
            activation_url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"
            send_mail(
                'Bienvenido a Lambda Commerce',
                f'Hola {usuario.nombre},\n\nHas sido registrado en Lambda Commerce.\n\nPara activar tu cuenta, haz clic en el siguiente enlace:\n{activation_url}\n\nEste enlace expira en 7 días.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )

            return Response({
                'mensaje': 'Usuario creado exitosamente. Se ha enviado un correo de activación.',
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            usuario = Usuario.objects.get(pk=pk)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_empresa
    def put(self, request, pk):
        try:
            usuario = Usuario.objects.get(pk=pk)
            serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'mensaje': 'Usuario actualizado exitosamente',
                    'usuario': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
