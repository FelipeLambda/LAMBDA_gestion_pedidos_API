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
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_grupos,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)
from Usuarios.models import Grupos


class EmpresaListCreateAPIView(SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        empresas = Empresa.activos.all()
        serializer = EmpresaSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    def post(self, request):
        serializer = EmpresaSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        empresa = serializer.save()
        token = secrets.token_urlsafe(32)
        empresa.token_activacion = token
        empresa.token_expiracion = timezone.now() + timedelta(days=7)
        empresa.save()
        EmailService.enviar_email_activacion_empresa(empresa, token)

        return Response({
            'mensaje': 'Empresa creada exitosamente. Se ha enviado un correo de activación.',
            'empresa': serializer.data
        }, status=status.HTTP_201_CREATED)


class EmpresaDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def get(self, request, pk):
        empresa, error = self.obtener_objeto_o_404(Empresa, pk)
        if error:
            return error

        serializer = EmpresaSerializer(empresa)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        empresa, error = self.obtener_objeto_o_404(Empresa, pk)
        if error:
            return error

        serializer = EmpresaSerializer(empresa, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({
            'mensaje': 'Empresa actualizada exitosamente',
            'empresa': serializer.data
        }, status=status.HTTP_200_OK)
