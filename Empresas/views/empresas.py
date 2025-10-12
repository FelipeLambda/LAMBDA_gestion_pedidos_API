import secrets
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from Empresas.models import Empresa, Area
from Empresas.serializers import EmpresaSerializer, ActivarEmpresaSerializer
from Usuarios.models import Usuario, Grupos
from Usuarios.serializers import UsuarioSerializer
from Usuarios.services import EmailService
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_grupos,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)


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


class ActivarEmpresaAPIView(SerializerValidationMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ActivarEmpresaSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        token = serializer.validated_data['token']

        try:
            empresa = Empresa.objects.get(token_activacion=token)
        except Empresa.DoesNotExist:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if empresa.token_expiracion < timezone.now():
            return Response({'error': 'El token ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(empresa=empresa, groups__name=Grupos.ADMIN_EMPRESA).exists():
            return Response(
                {'error': 'Esta empresa ya tiene un administrador registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        area_admin = Area.objects.create(
            nombre='Administración',
            empresa=empresa,
            descripcion='Área administrativa principal'
        )

        admin_empresa = Usuario.objects.create_user(
            email=serializer.validated_data['email'],
            nombre=serializer.validated_data['nombre'],
            cargo=serializer.validated_data['cargo'],
            password=serializer.validated_data['password'],
            empresa=empresa,
            area=area_admin
        )

        grupo_admin_empresa = Group.objects.get(name=Grupos.ADMIN_EMPRESA)
        admin_empresa.groups.add(grupo_admin_empresa)

        empresa.token_activacion = None
        empresa.token_expiracion = None
        empresa.save()

        return Response({
            'mensaje': 'Empresa activada exitosamente',
            'empresa': EmpresaSerializer(empresa).data,
            'usuario': UsuarioSerializer(admin_empresa).data
        }, status=status.HTTP_201_CREATED)


class RegenerarTokenEmpresaAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    def post(self, request, pk):
        empresa, error = self.obtener_objeto_o_404(Empresa, pk)
        if error:
            return error

        if Usuario.objects.filter(empresa=empresa, groups__name=Grupos.ADMIN_EMPRESA).exists():
            return Response(
                {'error': 'Esta empresa ya tiene un administrador. No se puede regenerar el token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = secrets.token_urlsafe(32)
        empresa.token_activacion = token
        empresa.token_expiracion = timezone.now() + timedelta(days=7)
        empresa.save()

        EmailService.enviar_email_activacion_empresa(empresa, token)

        return Response({
            'mensaje': 'Token regenerado exitosamente. Se ha enviado un nuevo correo de activación.',
            'token_expiracion': empresa.token_expiracion
        }, status=status.HTTP_200_OK)
