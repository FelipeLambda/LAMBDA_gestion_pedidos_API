from django.db import models
from django.core.exceptions import ValidationError
from Base.models import BaseModel, ActiveManager
from Empresas.models import Empresa, Area
from Usuarios.models import Usuario
from Productos.models import Producto


class SolicitudManager(models.Manager):
    """Manager personalizado para Solicitud con consultas específicas"""

    def pendientes(self):
        return self.filter(estado=True, estado_solicitud='PENDIENTE')

    def aprobadas(self):
        return self.filter(estado=True, estado_solicitud='APROBADA')

    def validadas_financiero(self):
        return self.filter(estado=True, estado_solicitud='VALIDADA_FINANCIERO')


class Solicitud(BaseModel):
    ESTADOS_SOLICITUD = [
        ('PENDIENTE', 'Pendiente'),
        ('VALIDADA_FINANCIERO', 'Validada por Financiero'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='solicitudes',
        verbose_name='Empresa'
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        related_name='solicitudes',
        null=True,
        blank=True,
        verbose_name='Área'
    )
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='solicitudes_creadas',
        verbose_name='Solicitante'
    )
    estado_solicitud = models.CharField(
        max_length=30,
        choices=ESTADOS_SOLICITUD,
        default='PENDIENTE',
        verbose_name='Estado de la solicitud'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones generales'
    )

    validador_financiero = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name='validaciones_financieras',
        null=True,
        blank=True,
        verbose_name='Validador Financiero'
    )
    fecha_validacion_financiero = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de validación financiera'
    )
    observaciones_financiero = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones del validador financiero'
    )

    validador_abastecimiento = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name='validaciones_abastecimiento',
        null=True,
        blank=True,
        verbose_name='Validador de Abastecimiento'
    )
    fecha_validacion_abastecimiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de validación de abastecimiento'
    )
    observaciones_abastecimiento = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones del validador de abastecimiento'
    )

    objects = SolicitudManager()
    activos = ActiveManager()

    class Meta:
        db_table = 'solicitudes'
        verbose_name = 'Solicitud'
        verbose_name_plural = 'Solicitudes'
        ordering = ['-fecha_creacion']
        permissions = [
            ('validar_financiero', 'Puede validar solicitudes financieramente'),
            ('validar_abastecimiento', 'Puede validar solicitudes de abastecimiento'),
        ]

    def __str__(self):
        return f"Solicitud #{self.id} - {self.solicitante.nombre} - {self.estado_solicitud}"

    def clean(self):
        if self.area and self.area.empresa != self.empresa:
            raise ValidationError('El área debe pertenecer a la empresa seleccionada.')

    @property
    def total(self):
        return sum(detalle.subtotal for detalle in self.detalles.all())

    @property
    def cantidad_items(self):
        return self.detalles.count()

    @property
    def esta_aprobada(self):
        """Verifica si la solicitud está completamente aprobada"""
        return self.estado_solicitud == 'APROBADA'

    @property
    def puede_convertirse_a_pedido(self):
        """Verifica si la solicitud puede convertirse en pedido"""
        return self.esta_aprobada


class DetalleSolicitud(BaseModel):
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Solicitud'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_solicitud',
        verbose_name='Producto'
    )
    cantidad = models.IntegerField(
        verbose_name='Cantidad solicitada'
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario'
    )

    class Meta:
        db_table = 'detalles_solicitud'
        verbose_name = 'Detalle de Solicitud'
        verbose_name_plural = 'Detalles de Solicitud'
        ordering = ['id']
        unique_together = ['solicitud', 'producto']

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        if self.precio_unitario < 0:
            raise ValidationError('El precio unitario no puede ser negativo.')

    @property
    def subtotal(self):
        """Calcula el subtotal del detalle"""
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
