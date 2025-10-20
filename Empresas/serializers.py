from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Empresa, Area


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nombre', 'sector', 'nit', 'nombre_contacto', 'correo_contacto', 'pagar_despues', 'periodo_pago_dias', 'estado', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


class AreaSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'nombre', 'descripcion', 'empresa', 'empresa_nombre', 'es_area_financiera', 'es_area_abastecimiento', 'estado', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def validate(self, attrs):
        if attrs.get('es_area_financiera') and attrs.get('es_area_abastecimiento'):
            raise serializers.ValidationError(
                "Un área no puede ser financiera y de abastecimiento al mismo tiempo"
            )
        return attrs


class ActivarEmpresaSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    nombre = serializers.CharField(required=True, max_length=200)
    email = serializers.EmailField(required=True)
    cargo = serializers.CharField(required=True, max_length=100)
    password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs
