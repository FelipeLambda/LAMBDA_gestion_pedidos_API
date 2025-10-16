from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from Base.models import BaseModel
from Empresas.models import Empresa, Area


class Grupos:
    ADMIN_SISTEMA = 'Admin Sistema'
    ADMIN_EMPRESA = 'Admin Empresa'
    JEFE_AREA = 'Jefe de Área'
    VALIDADOR_FINANCIERO = 'Validador Financiero'
    VALIDADOR_ABASTECIMIENTO = 'Validador Abastecimiento'
    SOLICITANTE = 'Solicitante'

    @classmethod
    def todos(cls):
        return [
            cls.ADMIN_SISTEMA,
            cls.ADMIN_EMPRESA,
            cls.JEFE_AREA,
            cls.VALIDADOR_FINANCIERO,
            cls.VALIDADOR_ABASTECIMIENTO,
            cls.SOLICITANTE
        ]


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nombre, cargo=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        extra_fields['nombre'] = nombre
        if cargo:
            extra_fields['cargo'] = cargo

        empresa_id = extra_fields.pop('empresa_id', None)
        area_id = extra_fields.pop('area_id', None)

        if empresa_id:
            try:
                extra_fields['empresa'] = Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist:
                raise ValueError(f'Empresa con ID {empresa_id} no existe')

        if area_id:
            try:
                extra_fields['area'] = Area.objects.get(pk=area_id)
            except Area.DoesNotExist:
                raise ValueError(f'Área con ID {area_id} no existe')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    nombre = models.CharField(max_length=200, verbose_name='Nombre completo')
    cargo = models.CharField(max_length=100, default='Sin cargo', verbose_name='Cargo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios', verbose_name='Empresa')
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='usuarios', verbose_name='Área')
    is_staff = models.BooleanField(default=False, verbose_name='¿Es staff?')
    is_active = models.BooleanField(default=True, verbose_name='¿Está activo?')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    token_activacion = models.CharField(max_length=100, blank=True, null=True, verbose_name='Token de activación')
    token_expiracion = models.DateTimeField(blank=True, null=True, verbose_name='Expiración del token')

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'cargo', 'empresa_id', 'area_id']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.nombre} ({self.email})".title()

    def validar_token_activacion(self, token):

        if not self.token_activacion:
            return False, 'No hay token de activación para este usuario.'

        if self.token_activacion != token:
            return False, 'Token de activación inválido.'

        if self.token_expiracion and timezone.now() > self.token_expiracion:
            return False, 'El token de activación ha expirado.'

        return True, None

    def activar_cuenta(self):
        self.is_active = True
        self.token_activacion = None
        self.token_expiracion = None
        self.save(update_fields=['is_active', 'token_activacion', 'token_expiracion'])

    def tiene_permiso_rbac(self, codigo_permiso):

        if self.is_superuser:
            return True

        return self.roles.filter(permisos__codigo=codigo_permiso).exists()


class Permiso(models.Model):
    """
    Permisos granulares del sistema.
    Estos son inmutables y definidos por LAMBDA.
    """
    MODULOS = [
        ('pedidos', 'Pedidos'),
        ('solicitudes', 'Solicitudes'),
        ('usuarios', 'Usuarios'),
        ('productos', 'Productos'),
        ('inventario', 'Inventario'),
        ('reportes', 'Reportes'),
        ('pagos', 'Pagos'),
        ('empresas', 'Empresas'),
    ]

    codigo = models.CharField(max_length=100, unique=True, verbose_name='Código del permiso')
    nombre = models.CharField(max_length=200, verbose_name='Nombre descriptivo')
    modulo = models.CharField(max_length=50, choices=MODULOS, verbose_name='Módulo')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'permisos'
        ordering = ['modulo', 'codigo']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Role(BaseModel):
    """
    Roles del sistema (empresa=NULL) o personalizados (empresa!=NULL).
    Los roles del sistema son templates base que todas las empresas pueden usar.
    """
    TIPO_CHOICES = [
        ('SISTEMA', 'Rol del Sistema'),
        ('PERSONALIZADO', 'Rol Personalizado'),
    ]

    nombre = models.CharField(max_length=100, verbose_name='Nombre del rol')
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name='Empresa',
        null=True,
        blank=True,
        help_text='NULL para roles del sistema, empresa específica para roles personalizados'
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='PERSONALIZADO',
        verbose_name='Tipo de rol'
    )
    es_modificable = models.BooleanField(
        default=True,
        verbose_name='¿Es modificable?',
        help_text='Los roles del sistema base no son modificables (pero se pueden clonar)'
    )
    creado_por = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_creados',
        verbose_name='Creado por'
    )
    permisos = models.ManyToManyField(
        Permiso,
        blank=True,
        related_name='roles',
        verbose_name='Permisos'
    )

    class Meta:
        db_table = 'roles'
        ordering = ['tipo', 'nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        if self.empresa:
            return f"{self.nombre} - {self.empresa.nombre}"
        return f"{self.nombre} (Sistema)"

    def es_rol_sistema(self):
        return self.tipo == 'SISTEMA' and self.empresa is None

    def puede_ser_editado_por(self, usuario):
        if usuario.is_superuser or usuario.groups.filter(name=Grupos.ADMIN_SISTEMA).exists():
            return True

        if self.es_rol_sistema() and not self.es_modificable:
            return False

        if usuario.groups.filter(name=Grupos.ADMIN_EMPRESA).exists():
            return self.empresa == usuario.empresa

        return False

    def clonar_para_empresa(self, empresa, usuario, nuevo_nombre=None):
        rol_clonado = Role.objects.create(
            nombre=nuevo_nombre or f"{self.nombre} (Copia)",
            empresa=empresa,
            descripcion=self.descripcion,
            tipo='PERSONALIZADO',
            es_modificable=True,
            creado_por=usuario
        )
        rol_clonado.permisos.set(self.permisos.all())
        return rol_clonado


Usuario.add_to_class('roles', models.ManyToManyField(Role, blank=True, related_name='usuarios'))
