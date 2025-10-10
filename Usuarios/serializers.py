from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    grupos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'cargo', 'empresa', 'empresa_nombre',
            'area', 'area_nombre', 'grupos',
            'is_active', 'date_joined', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'date_joined', 'fecha_creacion', 'fecha_actualizacion']

    def get_grupos(self, obj):
        return [grupo.name for grupo in obj.groups.all()]

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

        if attrs.get('area') and attrs.get('empresa'):
            if attrs['area'].empresa != attrs['empresa']:
                raise serializers.ValidationError({
                    "area": "El área debe pertenecer a la empresa seleccionada."
                })

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
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
            usuario = Usuario.objects.get(email=value)
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
