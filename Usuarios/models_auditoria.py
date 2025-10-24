from django.db import models
from django.conf import settings
from Base.models import BaseModel


class RegistroAuditoriaGrupo(BaseModel):
    usuario_modificador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modificaciones_grupos_realizadas',
        verbose_name='Usuario que realizó el cambio'
    )
    usuario_afectado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='modificaciones_grupos_recibidas',
        verbose_name='Usuario afectado'
    )
    accion = models.CharField(
        max_length=20,
        choices=[
            ('ASIGNAR', 'Asignar Grupo'),
            ('REMOVER', 'Remover Grupo')
        ],
        verbose_name='Acción'
    )
    grupo_nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del grupo'
    )
    empresa = models.ForeignKey(
        'Empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='auditorias_grupos',
        verbose_name='Empresa'
    )
    motivo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo del cambio'
    )

    class Meta:
        db_table = 'auditoria_grupos'
        verbose_name = 'Registro de Auditoría de Grupo'
        verbose_name_plural = 'Registros de Auditoría de Grupos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.usuario_modificador} {self.accion} {self.grupo_nombre} a {self.usuario_afectado}"
