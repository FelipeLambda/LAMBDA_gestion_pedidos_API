import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from Usuarios.models import Usuario
from Usuarios.serializers import (
    UsuarioSerializer, LoginSerializer,
    CambioPasswordSerializer, RecuperarPasswordSerializer, ResetPasswordSerializer
)
from Usuarios.services.email_service import EmailService
from LAMBDA_gestion_pedidos_API.utils import ObjetoDetailMixin, SerializerValidationMixin

class LoginAPIView(SerializerValidationMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        usuario = serializer.validated_data['usuario']
        refresh = RefreshToken.for_user(usuario)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'usuario': UsuarioSerializer(usuario).data
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'mensaje': 'Sesión cerrada exitosamente'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PerfilUsuarioAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Perfil actualizado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)


class CambioPasswordAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambioPasswordSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({'mensaje': 'Contraseña actualizada exitosamente'}, status=status.HTTP_200_OK)


class RecuperarPasswordAPIView(SerializerValidationMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecuperarPasswordSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        email = serializer.validated_data['email']
        usuario = Usuario.objects.get(email=email)

        token = secrets.token_urlsafe(32)
        usuario.token_activacion = token
        usuario.token_expiracion = timezone.now() + timedelta(hours=24)
        usuario.save()

        EmailService.enviar_email_recuperacion_password(usuario, token)

        return Response({'mensaje': 'Se ha enviado un correo con instrucciones para recuperar tu contraseña'}, status=status.HTTP_200_OK)


class ResetPasswordAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        token = serializer.validated_data['token']

        try:
            usuario = Usuario.objects.get(token_activacion=token)
        except Usuario.DoesNotExist:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if usuario.token_expiracion < timezone.now():
            return Response({'error': 'El token ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(serializer.validated_data['password_nuevo'])
        usuario.token_activacion = None
        usuario.token_expiracion = None
        usuario.save()

        return Response({'mensaje': 'Contraseña restablecida exitosamente'}, status=status.HTTP_200_OK)


class ActivarUsuarioAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')

        if not token or not password:
            return Response({'error': 'Token y contraseña son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(token_activacion=token)
        except Usuario.DoesNotExist:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if usuario.token_expiracion < timezone.now():
            return Response({'error': 'El token ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(password)
        usuario.is_active = True
        usuario.token_activacion = None
        usuario.token_expiracion = None
        usuario.save()

        return Response({
            'mensaje': 'Usuario activado exitosamente',
            'usuario': UsuarioSerializer(usuario).data
        }, status=status.HTTP_200_OK)
