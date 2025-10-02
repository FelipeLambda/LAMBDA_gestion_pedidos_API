from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Empresa, Area

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nombre', 'sector', 'nit', 'correo_contacto', 'pagar_despues', 'estado', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AreaSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'nombre', 'descripcion', 'empresa', 'empresa_nombre', 'estado', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UsuarioSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'cargo', 'empresa', 'empresa_nombre',
            'area', 'area_nombre', 'es_admin_sistema', 'es_admin_empresa',
            'es_validador_financiero', 'es_validador_abastecimiento', 'es_solicitante',
            'is_active', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'cargo', 'password', 'password2', 'empresa', 'area']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
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
