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
from LAMBDA_gestion_pedidos_API.utils import requiere_grupos, FiltradoEmpresaMixin, manejar_errores_db
from Usuarios.models import Grupos


class UsuarioListCreateAPIView(FiltradoEmpresaMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        usuarios = self.filtrar_por_empresa(request, Usuario.objects.all())
        serializer = UsuarioSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request):
        serializer = RegistroUsuarioSerializer(data=request.data)
        if serializer.is_valid():
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        try:
            usuario = Usuario.objects.get(pk=pk)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
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
