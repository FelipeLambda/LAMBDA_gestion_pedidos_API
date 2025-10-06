from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from Empresas.models import Empresa, Area

class Command(createsuperuser.Command):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--cargo',
            dest='cargo',
            default=None,
            help='Cargo del usuario',
        )
        parser.add_argument(
            '--empresa',
            dest='empresa',
            type=int,
            default=None,
            help='ID de la empresa',
        )
        parser.add_argument(
            '--area',
            dest='area',
            type=int,
            default=None,
            help='ID del área',
        )

    def handle(self, *args, **options):
        cargo = options.get('cargo')
        empresa_id = options.get('empresa')
        area_id = options.get('area')

        if options.get('interactive'):
            empresas = Empresa.activos.all()
            if not empresas.exists():
                raise CommandError('No hay empresas activas. Crea una empresa primero.')

            if not empresa_id:
                self.stdout.write('\nEmpresas disponibles:')
                for emp in empresas:
                    self.stdout.write(f'  [{emp.id}] {emp.nombre}')
                empresa_id = input('ID de la empresa: ')
                try:
                    empresa_id = int(empresa_id)
                except ValueError:
                    raise CommandError('ID de empresa inválido')

            try:
                empresa = Empresa.objects.get(pk=empresa_id)
            except Empresa.DoesNotExist:
                raise CommandError(f'Empresa con ID {empresa_id} no existe')

            areas = Area.activos.filter(empresa=empresa)
            if not areas.exists():
                raise CommandError(f'No hay áreas activas en la empresa {empresa.nombre}. Crea un área primero.')

            if not area_id:
                self.stdout.write(f'\nÁreas disponibles en {empresa.nombre}:')
                for a in areas:
                    self.stdout.write(f'  [{a.id}] {a.nombre}')
                area_id = input('ID del área: ')
                try:
                    area_id = int(area_id)
                except ValueError:
                    raise CommandError('ID de área inválido')

            try:
                area = Area.objects.get(pk=area_id)
            except Area.DoesNotExist:
                raise CommandError(f'Área con ID {area_id} no existe')

        options['empresa_id'] = empresa_id
        options['area_id'] = area_id
        options['cargo'] = cargo

        super().handle(*args, **options)
