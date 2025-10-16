from django.db import migrations


def crear_grupo_jefe_area(apps, schema_editor):
    """Crea el grupo 'Jefe de Área' en el sistema"""
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Jefe de Área')


def eliminar_grupo_jefe_area(apps, schema_editor):
    """Elimina el grupo 'Jefe de Área' (operación reversa)"""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Jefe de Área').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0002_registroauditoriagrupo'),
    ]

    operations = [
        migrations.RunPython(crear_grupo_jefe_area, eliminar_grupo_jefe_area),
    ]
