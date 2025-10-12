from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    """Manager que retorna solo objetos activos (estado=True)"""
    def get_queryset(self):
        return super().get_queryset().filter(estado=True)


class BaseModel(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    estado = models.BooleanField(default=True, verbose_name='Estado')

    objects = models.Manager()
    activos = ActiveManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """Desactiva el objeto (soft delete) en lugar de eliminarlo físicamente"""
        self.estado = False
        self.save(update_fields=['estado', 'fecha_actualizacion'])
