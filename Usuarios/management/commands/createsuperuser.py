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

        empresas = Empresa.activos.all()
        if not empresas.exists():
            raise CommandError('No hay empresas activas. Ejecuta "python manage.py inicializar_empresa_lambda" primero.')

        empresa_lambda = empresas.filter(nombre='LAMBDA').first()

        if not empresa_id:
            self.stdout.write('\n=== CREACIÓN DE SUPERUSUARIO ===')
            if empresa_lambda:
                self.stdout.write(self.style.WARNING(
                    f'\n[RECOMENDADO] Los superusuarios deben pertenecer a la empresa LAMBDA (ID: {empresa_lambda.id})'
                ))

            self.stdout.write('\n=== Empresas disponibles ===')
            for emp in empresas:
                marcador = ' [LAMBDA - RECOMENDADO]' if emp.nombre == 'LAMBDA' else ''
                self.stdout.write(f'  [{emp.id}] {emp.nombre}{marcador}')

            empresa_input = input(f'\nIngrese el ID de la empresa (recomendado: {empresa_lambda.id if empresa_lambda else ""}): ')

            if not empresa_input and empresa_lambda:
                empresa_id = empresa_lambda.id
                self.stdout.write(self.style.SUCCESS(f'[OK] Usando empresa LAMBDA (ID: {empresa_id})'))
            else:
                try:
                    empresa_id = int(empresa_input)
                except ValueError:
                    raise CommandError('ID de empresa inválido')

        try:
            empresa = Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise CommandError(f'Empresa con ID {empresa_id} no existe')

        areas = Area.activos.filter(empresa=empresa)
        if not areas.exists():
            raise CommandError(f'No hay áreas activas en la empresa {empresa.nombre}. Crea un área primero.')

        area_sistema = areas.filter(nombre='Administración del Sistema').first()

        if not area_id:
            self.stdout.write(f'\n=== Áreas disponibles en {empresa.nombre} ===')
            for a in areas:
                marcador = ' [ÁREA DE SISTEMA - RECOMENDADO]' if a.nombre == 'Administración del Sistema' else ''
                self.stdout.write(f'  [{a.id}] {a.nombre}{marcador}')

            area_input = input(f'\nIngrese el ID del área (recomendado: {area_sistema.id if area_sistema else ""}): ')

            if not area_input and area_sistema:
                area_id = area_sistema.id
                self.stdout.write(self.style.SUCCESS(f'[OK] Usando área "Administración del Sistema" (ID: {area_id})'))
            else:
                try:
                    area_id = int(area_input)
                except ValueError:
                    raise CommandError('ID de área inválido')

        try:
            area = Area.objects.get(pk=area_id)
        except Area.DoesNotExist:
            raise CommandError(f'Área con ID {area_id} no existe')

        if not cargo:
            cargo = 'Administrador del Sistema'

        options['empresa_id'] = empresa_id
        options['area_id'] = area_id
        options['cargo'] = cargo

        if empresa.nombre == 'LAMBDA' and area.nombre == 'Administración del Sistema':
            self.stdout.write(self.style.SUCCESS(
                '\n[OK] Configuración correcta: Superusuario en LAMBDA > Administración del Sistema'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n[ADVERTENCIA] Este superusuario pertenece a "{empresa.nombre} > {area.nombre}"'
            ))
            self.stdout.write(self.style.WARNING(
                'Se recomienda que los superusuarios pertenezcan a "LAMBDA > Administración del Sistema"'
            ))

        super().handle(*args, **options)
