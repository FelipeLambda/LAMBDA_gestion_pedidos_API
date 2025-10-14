from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Empresa, Area


@receiver(post_save, sender=Empresa)
def crear_areas_criticas(sender, instance, created, **kwargs):

    if not created and instance.token_activacion is None:
        empresa = instance

        if not Area.objects.filter(empresa=empresa, nombre='Administración').exists():
            Area.objects.create(
                nombre='Administración',
                empresa=empresa,
                descripcion='Área administrativa principal',
                es_area_financiera=False,
                es_area_abastecimiento=False
            )

        if not Area.objects.filter(empresa=empresa, es_area_financiera=True).exists():
            Area.objects.create(
                nombre='Finanzas',
                empresa=empresa,
                descripcion='Departamento de finanzas y contabilidad',
                es_area_financiera=True,
                es_area_abastecimiento=False
            )

        if not Area.objects.filter(empresa=empresa, es_area_abastecimiento=True).exists():
            Area.objects.create(
                nombre='Logística',
                empresa=empresa,
                descripcion='Departamento de logística y almacén',
                es_area_financiera=False,
                es_area_abastecimiento=True
            )
