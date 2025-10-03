import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from Empresas.models import Empresa
from Empresas.serializers import EmpresaSerializer
from LAMBDA_gestion_pedidos_API.utils import requiere_admin_sistema


class EmpresaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresas = Empresa.objects.filter(estado=True)
        serializer = EmpresaSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_admin_sistema
    def post(self, request):
        serializer = EmpresaSerializer(data=request.data)
        if serializer.is_valid():
            empresa = serializer.save()

            # Generar token de activación para el contacto inicial
            token = secrets.token_urlsafe(32)
            activation_url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"

            # Enviar email de activación
            send_mail(
                'Bienvenido a Lambda Commerce Solutions',
                f'Hola,\n\nTu empresa {empresa.nombre} ha sido registrada en Lambda Commerce.\n\nPara activar tu cuenta de administrador, haz clic en el siguiente enlace:\n{activation_url}\n\nEste enlace expira en 7 días.',
                settings.DEFAULT_FROM_EMAIL,
                [empresa.correo_contacto],
                fail_silently=False,
            )

            return Response({
                'mensaje': 'Empresa creada exitosamente. Se ha enviado un correo de activación.',
                'empresa': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmpresaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            empresa = Empresa.objects.get(pk=pk)
            serializer = EmpresaSerializer(empresa)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_sistema
    def put(self, request, pk):
        try:
            empresa = Empresa.objects.get(pk=pk)
            serializer = EmpresaSerializer(empresa, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'mensaje': 'Empresa actualizada exitosamente',
                    'empresa': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa no encontrada'}, status=status.HTTP_404_NOT_FOUND)
