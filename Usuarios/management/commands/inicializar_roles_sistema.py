from django.core.management.base import BaseCommand
from Usuarios.models import Permiso, Role, Grupos


class Command(BaseCommand):
    help = 'Inicializa los roles del sistema con sus permisos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Inicializando roles del sistema...'))

        # Definición de roles del sistema con sus permisos
        roles_sistema = {
            Grupos.ADMIN_SISTEMA: {
                'descripcion': 'Administrador global de LAMBDA con acceso total al sistema',
                'permisos': ['*'],  # Todos los permisos
                'es_modificable': False
            },
            Grupos.ADMIN_EMPRESA: {
                'descripcion': 'Administrador de la empresa con acceso completo a la gestión empresarial',
                'permisos': [
                    # Pedidos
                    'pedidos.ver', 'pedidos.crear', 'pedidos.editar_todos', 'pedidos.cancelar_todos',
                    'pedidos.aprobar_financiero', 'pedidos.aprobar_abastecimiento',
                    # Solicitudes
                    'solicitudes.ver', 'solicitudes.crear', 'solicitudes.editar_todos',
                    'solicitudes.validar_financiero', 'solicitudes.validar_abastecimiento',
                    'solicitudes.aprobar', 'solicitudes.rechazar',
                    # Usuarios
                    'usuarios.ver', 'usuarios.crear', 'usuarios.editar',
                    'usuarios.activar_desactivar', 'usuarios.asignar_roles', 'usuarios.gestionar_grupos',
                    # Productos
                    'productos.ver', 'productos.crear', 'productos.editar',
                    'productos.eliminar', 'productos.gestionar_categorias',
                    # Inventario
                    'inventario.ver', 'inventario.ajustar', 'inventario.ver_movimientos',
                    # Reportes
                    'reportes.ver_financiero', 'reportes.ver_inventario',
                    'reportes.ver_pedidos', 'reportes.ver_solicitudes', 'reportes.exportar',
                    # Pagos
                    'pagos.ver', 'pagos.registrar', 'pagos.validar',
                    # Empresas (solo su empresa)
                    'empresas.gestionar_areas',
                ],
                'es_modificable': True
            },
            Grupos.JEFE_AREA: {
                'descripcion': 'Jefe de área que gestiona usuarios y solicitudes de su área',
                'permisos': [
                    # Solicitudes (de su área)
                    'solicitudes.ver', 'solicitudes.crear', 'solicitudes.editar_propio',
                    # Pedidos (visualización)
                    'pedidos.ver',
                    # Usuarios (de su área)
                    'usuarios.ver',
                    # Productos
                    'productos.ver',
                    # Reportes
                    'reportes.ver_pedidos', 'reportes.ver_solicitudes',
                ],
                'es_modificable': True
            },
            Grupos.VALIDADOR_FINANCIERO: {
                'descripcion': 'Validador que aprueba solicitudes y pedidos desde perspectiva financiera',
                'permisos': [
                    # Solicitudes
                    'solicitudes.ver', 'solicitudes.validar_financiero',
                    # Pedidos
                    'pedidos.ver', 'pedidos.aprobar_financiero',
                    # Reportes
                    'reportes.ver_financiero', 'reportes.ver_pedidos', 'reportes.ver_solicitudes',
                    # Pagos
                    'pagos.ver', 'pagos.validar',
                ],
                'es_modificable': True
            },
            Grupos.VALIDADOR_ABASTECIMIENTO: {
                'descripcion': 'Validador que aprueba solicitudes y pedidos desde perspectiva de inventario',
                'permisos': [
                    # Solicitudes
                    'solicitudes.ver', 'solicitudes.validar_abastecimiento',
                    # Pedidos
                    'pedidos.ver', 'pedidos.aprobar_abastecimiento',
                    # Productos
                    'productos.ver',
                    # Inventario
                    'inventario.ver', 'inventario.ver_movimientos',
                    # Reportes
                    'reportes.ver_inventario', 'reportes.ver_pedidos', 'reportes.ver_solicitudes',
                ],
                'es_modificable': True
            },
            Grupos.SOLICITANTE: {
                'descripcion': 'Usuario base que puede crear solicitudes de productos',
                'permisos': [
                    # Solicitudes
                    'solicitudes.ver', 'solicitudes.crear', 'solicitudes.editar_propio',
                    # Pedidos (solo ver los suyos)
                    'pedidos.ver',
                    # Productos
                    'productos.ver',
                ],
                'es_modificable': True
            },
        }

        roles_creados = 0
        roles_actualizados = 0

        for nombre_rol, config in roles_sistema.items():
            # Crear o actualizar rol
            rol, creado = Role.objects.get_or_create(
                nombre=nombre_rol,
                empresa=None,  # Roles del sistema no tienen empresa
                defaults={
                    'descripcion': config['descripcion'],
                    'tipo': 'SISTEMA',
                    'es_modificable': config['es_modificable']
                }
            )

            if creado:
                roles_creados += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Rol creado: {nombre_rol}'))
            else:
                roles_actualizados += 1
                self.stdout.write(self.style.WARNING(f'  ↻ Rol actualizado: {nombre_rol}'))

            # Asignar permisos
            if config['permisos'] == ['*']:
                # Admin Sistema tiene todos los permisos
                todos_permisos = Permiso.objects.all()
                rol.permisos.set(todos_permisos)
                self.stdout.write(f'     → Asignados TODOS los permisos ({todos_permisos.count()})')
            else:
                # Asignar permisos específicos
                permisos = Permiso.objects.filter(codigo__in=config['permisos'])
                rol.permisos.set(permisos)
                self.stdout.write(f'     → Asignados {permisos.count()} permisos')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Roles del sistema inicializados:'))
        self.stdout.write(self.style.SUCCESS(f'   - Creados: {roles_creados}'))
        self.stdout.write(self.style.SUCCESS(f'   - Actualizados: {roles_actualizados}'))
        self.stdout.write(self.style.SUCCESS(f'   - Total: {roles_creados + roles_actualizados}'))
