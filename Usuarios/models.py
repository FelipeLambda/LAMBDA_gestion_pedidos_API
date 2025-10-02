from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from Base.models import BaseModel

class Empresa(BaseModel):
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la empresa')
    sector = models.CharField(max_length=100, verbose_name='Sector')
    nit = models.CharField(max_length=50, unique=True, verbose_name='NIT')
    correo_contacto = models.EmailField(verbose_name='Correo de contacto')
    pagar_despues = models.BooleanField(default=False, verbose_name='¿Autorizado para pago diferido?')

    class Meta:
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']
        permissions = (
            ('ver_todas_empresas', 'Puede ver todas las empresas'),
            ('crear_empresa', 'Puede crear empresas'),
            ('editar_empresa', 'Puede editar empresas'),
            ('autorizar_pago_diferido', 'Puede autorizar pago diferido'),
        )

    def __str__(self):
        return f"{self.nombre}".title()


class Area(BaseModel):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del área')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='areas', verbose_name='Empresa')

    class Meta:
        db_table = 'areas'
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['nombre']
        unique_together = ['nombre', 'empresa']
        permissions = (
            ('ver_areas_empresa', 'Puede ver áreas de su empresa'),
            ('crear_area', 'Puede crear áreas'),
            ('editar_area', 'Puede editar áreas'),
        )

    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre}".title()


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('es_admin_sistema', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    nombre = models.CharField(max_length=200, verbose_name='Nombre completo')
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cargo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True, verbose_name='Empresa')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, related_name='usuarios', null=True, blank=True, verbose_name='Área')
    es_admin_sistema = models.BooleanField(default=False, verbose_name='¿Es admin del sistema?')
    es_admin_empresa = models.BooleanField(default=False, verbose_name='¿Es admin de empresa?')
    es_validador_financiero = models.BooleanField(default=False, verbose_name='¿Es validador financiero?')
    es_validador_abastecimiento = models.BooleanField(default=False, verbose_name='¿Es validador de abastecimiento?')
    es_solicitante = models.BooleanField(default=False, verbose_name='¿Puede crear solicitudes?')
    is_staff = models.BooleanField(default=False, verbose_name='¿Es staff?')
    is_active = models.BooleanField(default=True, verbose_name='¿Está activo?')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    token_activacion = models.CharField(max_length=100, blank=True, null=True, verbose_name='Token de activación')
    token_expiracion = models.DateTimeField(blank=True, null=True, verbose_name='Expiración del token')

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
        permissions = (
            ('ver_usuarios_empresa', 'Puede ver usuarios de su empresa'),
            ('crear_usuario_empresa', 'Puede crear usuarios en su empresa'),
            ('editar_usuario_empresa', 'Puede editar usuarios de su empresa'),
            ('asignar_permisos_validador', 'Puede asignar permisos de validador'),
            ('gestionar_todos_usuarios', 'Puede gestionar todos los usuarios del sistema'),
        )

    def __str__(self):
        return f"{self.nombre} ({self.email})".title()
