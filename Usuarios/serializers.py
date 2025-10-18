from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Usuario, Role, Permiso


class UsuarioSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'cargo', 'empresa', 'empresa_nombre',
            'area', 'area_nombre', 'roles',
            'is_active', 'date_joined', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'date_joined', 'fecha_creacion', 'fecha_actualizacion']

    def get_roles(self, obj):
        return [{'id': r.id, 'nombre': r.nombre, 'tipo': r.tipo} for r in obj.roles.all()]

class PermisoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permiso
        fields = ['id', 'codigo', 'nombre', 'modulo', 'descripcion']
        read_only_fields = ['id', 'codigo', 'nombre', 'modulo', 'descripcion']


class RoleSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True, allow_null=True)
    permisos = PermisoSerializer(many=True, read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True, allow_null=True)
    cantidad_permisos = serializers.SerializerMethodField()
    es_del_sistema = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'nombre', 'descripcion', 'tipo', 'empresa', 'empresa_nombre',
            'es_modificable', 'creado_por', 'creado_por_nombre', 'permisos',
            'cantidad_permisos', 'es_del_sistema', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'tipo', 'creado_por', 'fecha_creacion', 'fecha_actualizacion']

    def get_cantidad_permisos(self, obj):
        return obj.permisos.count()

    def get_es_del_sistema(self, obj):
        return obj.es_rol_sistema()


class RoleSimpleSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True, allow_null=True)
    cantidad_permisos = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'nombre', 'descripcion', 'tipo', 'empresa', 'empresa_nombre',
            'es_modificable', 'cantidad_permisos'
        ]

    def get_cantidad_permisos(self, obj):
        return obj.permisos.count()


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    permisos_codigos = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text='Lista de códigos de permisos a asignar (ej: ["pedidos.ver", "pedidos.crear"])'
    )

    class Meta:
        model = Role
        fields = ['nombre', 'descripcion', 'permisos_codigos']

    def validate_nombre(self, value):
        request = self.context.get('request')
        empresa = request.user.empresa if request else None
        instance = self.instance

        if instance:
            if Role.objects.filter(nombre=value, empresa=empresa).exclude(id=instance.id).exists():
                raise serializers.ValidationError(f"Ya existe un rol llamado '{value}' en tu empresa.")
        else:
            if Role.objects.filter(nombre=value, empresa=empresa).exists():
                raise serializers.ValidationError(f"Ya existe un rol llamado '{value}' en tu empresa.")

        return value

    def validate_permisos_codigos(self, value):
        if not value:
            return []

        permisos_invalidos = []
        for codigo in value:
            if not Permiso.objects.filter(codigo=codigo).exists():
                permisos_invalidos.append(codigo)

        if permisos_invalidos:
            raise serializers.ValidationError(
                f"Los siguientes permisos no existen: {', '.join(permisos_invalidos)}"
            )

        return value

    def create(self, validated_data):
        permisos_codigos = validated_data.pop('permisos_codigos', [])
        request = self.context.get('request')

        rol = Role.objects.create(
            nombre=validated_data['nombre'],
            descripcion=validated_data.get('descripcion', ''),
            empresa=request.user.empresa,
            tipo='PERSONALIZADO',
            es_modificable=True,
            creado_por=request.user
        )

        if permisos_codigos:
            permisos = Permiso.objects.filter(codigo__in=permisos_codigos)
            rol.permisos.set(permisos)

        return rol

    def update(self, instance, validated_data):
        permisos_codigos = validated_data.pop('permisos_codigos', None)

        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.save()

        if permisos_codigos is not None:
            permisos = Permiso.objects.filter(codigo__in=permisos_codigos)
            instance.permisos.set(permisos)

        return instance


class ClonarRolSerializer(serializers.Serializer):
    rol_id = serializers.IntegerField(required=True, help_text='ID del rol a clonar')
    nuevo_nombre = serializers.CharField(required=True, max_length=100, help_text='Nombre para el rol clonado')

    def validate_rol_id(self, value):
        try:
            rol = Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"No existe un rol con ID {value}")

        if not rol.es_rol_sistema():
            raise serializers.ValidationError("Solo se pueden clonar roles del sistema")

        return value

    def validate_nuevo_nombre(self, value):
        request = self.context.get('request')
        empresa = request.user.empresa if request else None

        if Role.objects.filter(nombre=value, empresa=empresa).exists():
            raise serializers.ValidationError(f"Ya existe un rol llamado '{value}' en tu empresa")

        return value


class AsignarRolSerializer(serializers.Serializer):
    rol_id = serializers.IntegerField(required=True, help_text='ID del rol a asignar')

    def validate_rol_id(self, value):
        request = self.context.get('request')

        try:
            rol = Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"No existe un rol con ID {value}")

        if rol.empresa and rol.empresa != request.user.empresa:
            raise serializers.ValidationError("No puedes asignar roles de otras empresas")

        return value


class RemoverRolSerializer(serializers.Serializer):
    rol_id = serializers.IntegerField(required=True, help_text='ID del rol a remover')

    def validate_rol_id(self, value):
        try:
            Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"No existe un rol con ID {value}")

        return value

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'cargo', 'password', 'password2', 'empresa', 'area']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        if not attrs.get('empresa'):
            raise serializers.ValidationError({
                "empresa": "La empresa es obligatoria para crear usuarios."
            })

        if not attrs.get('area'):
            raise serializers.ValidationError({
                "area": "El área es obligatoria para crear usuarios."
            })

        if attrs['area'].empresa != attrs['empresa']:
            raise serializers.ValidationError({
                "area": "El área debe pertenecer a la empresa seleccionada."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        usuario = Usuario.objects.create_user(**validated_data)
        return usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            usuario = authenticate(request=self.context.get('request'), email=email, password=password)

            if not usuario:
                raise serializers.ValidationError('Credenciales incorrectas.')

            if not usuario.is_active:
                raise serializers.ValidationError('Usuario inactivo.')

            attrs['usuario'] = usuario
            return attrs
        else:
            raise serializers.ValidationError('Debe incluir email y contraseña.')


class CambioPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True, required=True)
    password_nuevo = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_nuevo2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['password_nuevo'] != attrs['password_nuevo2']:
            raise serializers.ValidationError({"password_nuevo": "Las contraseñas no coinciden."})
        return attrs

    def validate_password_actual(self, value):
        usuario = self.context['request'].user
        if not usuario.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def save(self, **kwargs):
        usuario = self.context['request'].user
        usuario.set_password(self.validated_data['password_nuevo'])
        usuario.save()
        return usuario


class RecuperarPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            Usuario.objects.get(email=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("No existe un usuario con este correo.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password_nuevo = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_nuevo2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['password_nuevo'] != attrs['password_nuevo2']:
            raise serializers.ValidationError({"password_nuevo": "Las contraseñas no coinciden."})
        return attrs
