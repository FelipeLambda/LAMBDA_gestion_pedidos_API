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
                content_type__app_label__in=['Empresas', 'Usuarios', 'Productos', 'Base']
            )
            admin_sistema.permissions.set(todos_permisos)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Admin Sistema: {todos_permisos.count()} permisos asignados')
            )

            permisos_admin_empresa = Permission.objects.filter(
                codename__in=[
                    'add_usuario', 'change_usuario', 'view_usuario',
                    'add_area', 'change_area', 'view_area',
                    'view_empresa',
                    'view_producto', 'view_categoria',
                    'autorizar_pago_diferido',
                ]
            )
            admin_empresa.permissions.set(permisos_admin_empresa)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Admin Empresa: {permisos_admin_empresa.count()} permisos asignados')
            )

            permisos_validadores = Permission.objects.filter(
                codename__in=[
                    'view_usuario', 'view_empresa', 'view_area',
                    'view_producto', 'view_categoria',
                ]
            )

            for validador in [validador_financiero, validador_abastecimiento]:
                validador.permissions.set(permisos_validadores)
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] {validador.name}: {permisos_validadores.count()} permisos asignados')
                )

            permisos_solicitante = Permission.objects.filter(
                codename__in=[
                    'view_producto', 'view_categoria',
                ]
            )
            solicitante.permissions.set(permisos_solicitante)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Solicitante: {permisos_solicitante.count()} permisos asignados')
            )

            self.stdout.write(
                self.style.SUCCESS('\nPermisos asignados exitosamente a todos los grupos!')
            )

        except Group.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'\n[ERROR] Grupo no encontrado: {e}')
            )
            self.stdout.write(
                self.style.WARNING('Ejecuta primero: python manage.py inicializar_grupos')
            )
