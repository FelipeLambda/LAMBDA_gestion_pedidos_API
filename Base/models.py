from django.db import models

class BaseModel(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    estado = models.BooleanField(default=True, verbose_name='Estado')

    class Meta:
        abstract = True
