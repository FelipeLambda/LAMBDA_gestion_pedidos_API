from django.core.management.base import BaseCommand
from Empresas.models import Empresa, Area
from Usuarios.models import Usuario, Grupos, Role


class Command(BaseCommand):
    help = 'Inicializa la empresa LAMBDA con usuario administrador del sistema'

    def handle(self, *args, **kwargs):
        empresa_lambda, created = Empresa.objects.get_or_create(
            nit='900123456-7',
            defaults={
                'nombre': 'LAMBDA',
                'sector': 'Tecnología',
                'nombre_contacto': 'Administrador LAMBDA',
                'correo_contacto': 'admin@lambda.com',
                'pagar_despues': False,
                'estado': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Empresa LAMBDA creada'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] Empresa LAMBDA ya existe'))

        area_admin, created = Area.objects.get_or_create(
            nombre='Administración',
            empresa=empresa_lambda,
            defaults={
                'descripcion': 'Área administrativa de LAMBDA',
                'estado': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('[OK] Área Administración creada'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] Área Administración ya existe'))

        admin_email = 'admin@lambda.com'
        if not Usuario.objects.filter(email=admin_email).exists():
            admin = Usuario.objects.create_superuser(
                email=admin_email,
                nombre='Administrador LAMBDA',
                cargo='Administrador del Sistema',
                password='lambda123',
                empresa=empresa_lambda,
                area=area_admin
            )

            rol_admin_sistema = Role.objects.get(nombre=Grupos.ADMIN_SISTEMA, empresa=None)
            admin.roles.add(rol_admin_sistema)

            self.stdout.write(self.style.SUCCESS('[OK] Usuario admin@lambda.com creado'))
            self.stdout.write(self.style.WARNING('[IMPORTANTE] Contraseña temporal: lambda123'))
        else:
            self.stdout.write(self.style.WARNING('[INFO] Usuario admin@lambda.com ya existe'))

        self.stdout.write(self.style.SUCCESS('\nInicialización de empresa LAMBDA completada'))
