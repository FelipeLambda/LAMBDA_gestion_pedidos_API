import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Empresas.models import Empresa
from Empresas.serializers import EmpresaSerializer
from Usuarios.services import EmailService
from LAMBDA_gestion_pedidos_API.utils import requiere_admin_sistema, requiere_admin_empresa, manejar_errores_db


class EmpresaListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_admin_empresa
    def get(self, request):
        empresas = Empresa.activos.all()
        serializer = EmpresaSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_admin_sistema
    def post(self, request):
        serializer = EmpresaSerializer(data=request.data)
        if serializer.is_valid():
            empresa = serializer.save()
            token = secrets.token_urlsafe(32)
            EmailService.enviar_email_activacion_empresa(empresa, token)

            return Response({
                'mensaje': 'Empresa creada exitosamente. Se ha enviado un correo de activación.',
                'empresa': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmpresaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_admin_empresa
    @manejar_errores_db
    def get(self, request, pk):
        try:
            empresa = Empresa.objects.get(pk=pk)
            serializer = EmpresaSerializer(empresa)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    @requiere_admin_sistema
    @manejar_errores_db
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
