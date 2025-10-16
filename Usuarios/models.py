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


class Role(BaseModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del rol')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='roles', verbose_name='Empresa')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'roles'
        unique_together = [['nombre', 'empresa']]
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre}"

Usuario.add_to_class('roles', models.ManyToManyField(Role, blank=True, related_name='usuarios'))
