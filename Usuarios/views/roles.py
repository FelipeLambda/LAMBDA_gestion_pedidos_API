from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Usuarios.models import Role, Grupos
from Usuarios.serializers import RoleSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_grupos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)


class RoleListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def get(self, request):
        roles = self.filtrar_por_empresa(request, Role.objects.all())
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error
        if not request.user.is_superuser and request.user.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            role = serializer.save(empresa=request.user.empresa)
        else:
            role = serializer.save()

        return Response({
            'mensaje': 'Role creado exitosamente',
            'role': RoleSerializer(role).data
        }, status=status.HTTP_201_CREATED)


class RoleDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def get(self, request, pk):
        role, error = self.obtener_objeto_o_404(Role, pk)
        if error:
            return error

        serializer = RoleSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def put(self, request, pk):
        role, error = self.obtener_objeto_o_404(Role, pk)
        if error:
            return error

        if not request.user.is_superuser and role.empresa != request.user.empresa:
            return Response({'error': 'No puedes editar roles de otra empresa'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RoleSerializer(role, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        serializer.save()
        return Response({'mensaje': 'Role actualizado', 'role': serializer.data}, status=status.HTTP_200_OK)

    @requiere_grupos(Grupos.ADMIN_EMPRESA, Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def delete(self, request, pk):
        role, error = self.obtener_objeto_o_404(Role, pk)
        if error:
            return error

        if not request.user.is_superuser and role.empresa != request.user.empresa:
            return Response({'error': 'No puedes eliminar roles de otra empresa'}, status=status.HTTP_403_FORBIDDEN)

        role.delete()
        return Response({'mensaje': 'Role eliminado exitosamente'}, status=status.HTTP_200_OK)