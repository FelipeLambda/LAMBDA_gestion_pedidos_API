from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from Usuarios.models import Usuario, Role, Grupos


class Command(BaseCommand):
    help = 'Migra usuarios con grupos Django a roles RBAC del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se realizarán cambios en la base de datos\n'))
        else:
            self.stdout.write(self.style.WARNING('Iniciando migración de grupos a roles RBAC...\n'))

        # Mapeo de nombres de grupos a roles del sistema
        mapeo_grupos_roles = {
            Grupos.ADMIN_SISTEMA: 'Admin Sistema',
            Grupos.ADMIN_EMPRESA: 'Admin Empresa',
            Grupos.JEFE_AREA: 'Jefe de Área',
            Grupos.VALIDADOR_FINANCIERO: 'Validador Financiero',
            Grupos.VALIDADOR_ABASTECIMIENTO: 'Validador Abastecimiento',
            Grupos.SOLICITANTE: 'Solicitante',
        }

        usuarios_migrados = 0
        roles_asignados = 0
        errores = 0

        # Obtener todos los usuarios
        usuarios = Usuario.objects.all()
        total_usuarios = usuarios.count()

        self.stdout.write(f'Total de usuarios a procesar: {total_usuarios}\n')

        for usuario in usuarios:
            # Obtener grupos del usuario
            grupos_usuario = usuario.groups.values_list('name', flat=True)

            if not grupos_usuario:
                continue

            self.stdout.write(f'\nProcesando: {usuario.nombre} ({usuario.email})')
            self.stdout.write(f'  Grupos actuales: {", ".join(grupos_usuario)}')

            usuario_modificado = False

            for nombre_grupo in grupos_usuario:
                if nombre_grupo not in mapeo_grupos_roles:
                    self.stdout.write(self.style.WARNING(f'    ⚠ Grupo "{nombre_grupo}" no tiene mapeo a rol RBAC'))
                    continue

                # Buscar el rol del sistema correspondiente
                try:
                    rol = Role.objects.get(
                        nombre=mapeo_grupos_roles[nombre_grupo],
                        tipo='SISTEMA',
                        empresa=None
                    )
                except Role.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f'    ✗ Rol "{mapeo_grupos_roles[nombre_grupo]}" no existe. '
                        f'Ejecuta primero: python manage.py inicializar_roles_sistema'
                    ))
                    errores += 1
                    continue

                # Verificar si el usuario ya tiene este rol
                if usuario.roles.filter(id=rol.id).exists():
                    self.stdout.write(f'    → Ya tiene rol: {rol.nombre}')
                    continue

                # Asignar el rol
                if not dry_run:
                    usuario.roles.add(rol)
                    roles_asignados += 1
                    usuario_modificado = True
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Rol asignado: {rol.nombre}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'    [DRY-RUN] Se asignaría rol: {rol.nombre}'))
                    roles_asignados += 1

            if usuario_modificado:
                usuarios_migrados += 1

        # Resumen
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('\n✅ Migración completada\n'))
        self.stdout.write(f'   - Usuarios procesados: {total_usuarios}')
        self.stdout.write(f'   - Usuarios migrados: {usuarios_migrados}')
        self.stdout.write(f'   - Roles asignados: {roles_asignados}')

        if errores > 0:
            self.stdout.write(self.style.ERROR(f'   - Errores: {errores}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ MODO DRY-RUN: No se realizaron cambios en la BD'))
            self.stdout.write('Ejecuta sin --dry-run para aplicar los cambios')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Los usuarios ahora tienen roles RBAC asignados'))
            self.stdout.write('\nNOTA: Los grupos Django antiguos NO se han eliminado.')
            self.stdout.write('Esto permite mantener compatibilidad durante la transición.')
            self.stdout.write('Una vez migrado todo el código a usar @requiere_permisos,')
            self.stdout.write('podrás deprecar completamente los grupos Django.')
