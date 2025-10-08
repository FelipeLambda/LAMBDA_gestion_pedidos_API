from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.stdout.write('\nAsignando permisos a grupos...\n')

        try:
            admin_sistema = Group.objects.get(name='Admin Sistema')
            admin_empresa = Group.objects.get(name='Admin Empresa')
            validador_financiero = Group.objects.get(name='Validador Financiero')
            validador_abastecimiento = Group.objects.get(name='Validador Abastecimiento')
            solicitante = Group.objects.get(name='Solicitante')

            todos_permisos = Permission.objects.filter(
                content_type__app_label__in=['Empresas', 'Usuarios', 'Productos', 'Solicitudes', 'Base']
            )
            admin_sistema.permissions.set(todos_permisos)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Admin Sistema: {todos_permisos.count()} permisos asignados')
            )

            admin_empresa.permissions.clear()
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Admin Empresa: sin permisos custom (acceso controlado por grupo)')
            )

            permisos_validador_financiero = Permission.objects.filter(
                codename__in=[
                    'validar_financiero',
                ]
            )
            validador_financiero.permissions.set(permisos_validador_financiero)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Validador Financiero: {permisos_validador_financiero.count()} permisos asignados')
            )

            permisos_validador_abastecimiento = Permission.objects.filter(
                codename__in=[
                    'validar_abastecimiento',
                ]
            )
            validador_abastecimiento.permissions.set(permisos_validador_abastecimiento)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Validador Abastecimiento: {permisos_validador_abastecimiento.count()} permisos asignados')
            )

            solicitante.permissions.clear()
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Solicitante: sin permisos (acceso controlado por grupo)')
            )

            self.stdout.write(
                self.style.SUCCESS('\nPermisos custom asignados exitosamente a todos los grupos!')
            )

        except Group.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'\n[ERROR] Grupo no encontrado: {e}')
            )
            self.stdout.write(
                self.style.WARNING('Ejecuta primero: python manage.py inicializar_grupos')
            )
