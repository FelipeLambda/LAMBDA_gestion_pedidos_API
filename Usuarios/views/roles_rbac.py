from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Usuarios.models import Usuario, Role, Permiso, Grupos
from Usuarios.serializers import (
    PermisoSerializer,
    RoleSerializer,
    RoleSimpleSerializer,
    RoleCreateUpdateSerializer,
    ClonarRolSerializer,
    AsignarRolSerializer,
    RemoverRolSerializer,
    UsuarioSerializer
)
from LAMBDA_gestion_pedidos_API.utils import (
    requiere_permisos,
    FiltradoEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db
)


class ListarPermisosAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.listar_permisos')
    def get(self, request):
        permisos = Permiso.objects.all()

        permisos_por_modulo = {}
        for permiso in permisos:
            if permiso.modulo not in permisos_por_modulo:
                permisos_por_modulo[permiso.modulo] = []
            permisos_por_modulo[permiso.modulo].append({
                'id': permiso.id,
                'codigo': permiso.codigo,
                'nombre': permiso.nombre,
                'descripcion': permiso.descripcion
            })

        return Response({
            'permisos_por_modulo': permisos_por_modulo,
            'total_permisos': permisos.count()
        }, status=status.HTTP_200_OK)


class RolesRBACListCreateAPIView(FiltradoEmpresaMixin, SerializerValidationMixin, APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.listar')
    def get(self, request):
        roles_sistema = Role.objects.filter(tipo='SISTEMA', empresa=None)

        roles_personalizados = Role.objects.filter(
            tipo='PERSONALIZADO',
            empresa=request.user.empresa
        )

        return Response({
            'roles_sistema': RoleSimpleSerializer(roles_sistema, many=True).data,
            'roles_personalizados': RoleSimpleSerializer(roles_personalizados, many=True).data,
            'total_sistema': roles_sistema.count(),
            'total_personalizados': roles_personalizados.count()
        }, status=status.HTTP_200_OK)

    @requiere_permisos('roles.crear')
    @manejar_errores_db
    def post(self, request):
        serializer = RoleCreateUpdateSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        rol = serializer.save()

        return Response({
            'mensaje': f'Rol "{rol.nombre}" creado exitosamente',
            'rol': RoleSerializer(rol).data
        }, status=status.HTTP_201_CREATED)


class RolesRBACDetailAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.ver')
    @manejar_errores_db
    def get(self, request, pk):
        rol, error = self.obtener_objeto_o_404(Role, pk, usar_soft_delete=False)
        if error:
            return error

        if rol.empresa and rol.empresa != request.user.empresa and not request.user.is_superuser:
            return Response(
                {'error': 'No tienes permiso para ver este rol'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(RoleSerializer(rol).data, status=status.HTTP_200_OK)

    @requiere_permisos('roles.editar')
    @manejar_errores_db
    def put(self, request, pk):
        rol, error = self.obtener_objeto_o_404(Role, pk, usar_soft_delete=False)
        if error:
            return error

        if not rol.puede_ser_editado_por(request.user):
            return Response(
                {'error': 'No tienes permiso para editar este rol. Los roles del sistema no son modificables, pero puedes clonarlos.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RoleCreateUpdateSerializer(rol, data=request.data, partial=True, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        rol = serializer.save()

        return Response({
            'mensaje': f'Rol "{rol.nombre}" actualizado exitosamente',
            'rol': RoleSerializer(rol).data
        }, status=status.HTTP_200_OK)

    @requiere_permisos('roles.eliminar')
    @manejar_errores_db
    def delete(self, request, pk):
        rol, error = self.obtener_objeto_o_404(Role, pk, usar_soft_delete=False)
        if error:
            return error

        if not rol.puede_ser_editado_por(request.user):
            return Response(
                {'error': 'No tienes permiso para eliminar este rol'},
                status=status.HTTP_403_FORBIDDEN
            )

        if rol.es_rol_sistema():
            return Response(
                {'error': 'No se pueden eliminar roles del sistema'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuarios_con_rol = rol.usuarios.count()
        if usuarios_con_rol > 0:
            return Response(
                {'error': f'No se puede eliminar el rol porque {usuarios_con_rol} usuario(s) lo tienen asignado. Primero remueve el rol de esos usuarios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        nombre_rol = rol.nombre
        rol.delete()

        return Response({
            'mensaje': f'Rol "{nombre_rol}" eliminado exitosamente'
        }, status=status.HTTP_200_OK)


class ClonarRolAPIView(SerializerValidationMixin, APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.clonar')
    @manejar_errores_db
    def post(self, request):
        serializer = ClonarRolSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        rol_original = Role.objects.get(id=serializer.validated_data['rol_id'])
        nuevo_nombre = serializer.validated_data['nuevo_nombre']

        rol_clonado = rol_original.clonar_para_empresa(
            empresa=request.user.empresa,
            usuario=request.user,
            nuevo_nombre=nuevo_nombre
        )

        return Response({
            'mensaje': f'Rol "{rol_original.nombre}" clonado exitosamente como "{nuevo_nombre}"',
            'rol_original': RoleSimpleSerializer(rol_original).data,
            'rol_clonado': RoleSerializer(rol_clonado).data
        }, status=status.HTTP_201_CREATED)


class AsignarRolUsuarioAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.asignar_rol_usuario')
    @manejar_errores_db
    def post(self, request, pk):
        usuario_target, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        if usuario_target.empresa != request.user.empresa and not request.user.is_superuser:
            return Response(
                {'error': 'Solo puedes asignar roles a usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AsignarRolSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        rol = Role.objects.get(id=serializer.validated_data['rol_id'])

        if usuario_target.roles.filter(id=rol.id).exists():
            return Response(
                {'error': f'El usuario ya tiene el rol "{rol.nombre}"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario_target.roles.add(rol)

        return Response({
            'mensaje': f'Rol "{rol.nombre}" asignado exitosamente a {usuario_target.nombre}',
            'usuario': UsuarioSerializer(usuario_target).data
        }, status=status.HTTP_200_OK)


class RemoverRolUsuarioAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):

    permission_classes = [IsAuthenticated]

    @requiere_permisos('roles.remover_rol_usuario')
    @manejar_errores_db
    def post(self, request, pk):
        usuario_target, error = self.obtener_objeto_o_404(Usuario, pk, usar_soft_delete=False)
        if error:
            return error

        if usuario_target.empresa != request.user.empresa and not request.user.is_superuser:
            return Response(
                {'error': 'Solo puedes remover roles de usuarios de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RemoverRolSerializer(data=request.data, context={'request': request})
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        rol = Role.objects.get(id=serializer.validated_data['rol_id'])

        if not usuario_target.roles.filter(id=rol.id).exists():
            return Response(
                {'error': f'El usuario no tiene el rol "{rol.nombre}"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario_target.roles.remove(rol)

        return Response({
            'mensaje': f'Rol "{rol.nombre}" removido exitosamente de {usuario_target.nombre}',
            'usuario': UsuarioSerializer(usuario_target).data
        }, status=status.HTTP_200_OK)
