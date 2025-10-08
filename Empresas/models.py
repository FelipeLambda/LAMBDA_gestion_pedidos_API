from django.db import models
from Base.models import BaseModel

class Empresa(BaseModel):
    nombre = models.CharField(max_length=200, verbose_name='Nombre de la empresa')
    sector = models.CharField(max_length=100, verbose_name='Sector')
    nit = models.CharField(max_length=20, unique=True, verbose_name='NIT')
    nombre_contacto = models.CharField(max_length=200, default='Sin contacto', verbose_name='Nombre del contacto')
    correo_contacto = models.EmailField(verbose_name='Correo de contacto')
    pagar_despues = models.BooleanField(default=False, verbose_name='¿Autorizado para pago diferido?')
    token_activacion = models.CharField(max_length=100, blank=True, null=True, verbose_name='Token de activación')
    token_expiracion = models.DateTimeField(blank=True, null=True, verbose_name='Expiración del token')

    class Meta:
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre.title()


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

    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre}".title()
