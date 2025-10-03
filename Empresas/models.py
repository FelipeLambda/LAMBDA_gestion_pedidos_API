from django.db import models
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
