import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from Usuarios.models import Usuario
from Usuarios.serializers import (
    UsuarioSerializer, RegistroUsuarioSerializer, LoginSerializer,
    CambioPasswordSerializer, RecuperarPasswordSerializer, ResetPasswordSerializer
)


class RegistroUsuarioAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            return Response({
                'mensaje': 'Usuario registrado exitosamente',
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            usuario = serializer.validated_data['usuario']
            refresh = RefreshToken.for_user(usuario)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': UsuarioSerializer(usuario).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class PerfilUsuarioAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'mensaje': 'Perfil actualizado exitosamente',
                'usuario': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CambioPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambioPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Contraseña actualizada exitosamente'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecuperarPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecuperarPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            usuario = Usuario.objects.get(email=email)

            token = secrets.token_urlsafe(32)
            usuario.token_activacion = token
            usuario.token_expiracion = timezone.now() + timedelta(hours=24)
            usuario.save()

            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            send_mail(
                'Recuperación de contraseña - Lambda Commerce',
                f'Hola {usuario.nombre},\n\nPara restablecer tu contraseña, haz clic en el siguiente enlace:\n{reset_url}\n\nEste enlace expira en 24 horas.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )

            return Response({'mensaje': 'Se ha enviado un correo con instrucciones para recuperar tu contraseña'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']

            try:
                usuario = Usuario.objects.get(token_activacion=token)

                if usuario.token_expiracion < timezone.now():
                    return Response({'error': 'El token ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

                usuario.set_password(serializer.validated_data['password_nuevo'])
                usuario.token_activacion = None
                usuario.token_expiracion = None
                usuario.save()

                return Response({'mensaje': 'Contraseña restablecida exitosamente'}, status=status.HTTP_200_OK)
            except Usuario.DoesNotExist:
                return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivarUsuarioAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')

        if not token or not password:
            return Response({'error': 'Token y contraseña son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(token_activacion=token)

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
        except Usuario.DoesNotExist:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)
