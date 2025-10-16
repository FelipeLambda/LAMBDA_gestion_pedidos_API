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
    allowed_encargado_roles = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=None)
    encargado = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=None)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from Usuarios.models import Role, Usuario
        self.fields['allowed_encargado_roles'].queryset = Role.objects.all()
        self.fields['encargado'].queryset = Usuario.objects.all()

    def validate(self, attrs):
        base = super().validate(attrs)

        empresa = attrs.get('empresa') or getattr(self.instance, 'empresa', None)
        encargado = attrs.get('encargado') if 'encargado' in attrs else getattr(self.instance, 'encargado', None)
        allowed_roles = attrs.get('allowed_encargado_roles') if 'allowed_encargado_roles' in attrs else None

        if encargado and empresa and encargado.empresa_id != empresa.id:
            raise serializers.ValidationError({
                'encargado': 'El encargado debe pertenecer a la misma empresa que el área.'
            })

        if encargado and allowed_roles:
            encarg_role_ids = set(encargado.roles.filter(id__in=[r.id for r in allowed_roles]).values_list('id', flat=True))
            if not encarg_role_ids:
                raise serializers.ValidationError({
                    'encargado': 'El encargado no tiene ninguno de los roles permitidos para esta área.'
                })

        return base


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
