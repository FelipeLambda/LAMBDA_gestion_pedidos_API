from django.core.management.base import BaseCommand
from Usuarios.models import Permiso


class Command(BaseCommand):
    help = 'Inicializa los permisos granulares del sistema RBAC'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Inicializando permisos del sistema RBAC...'))

        permisos_data = [
            # PEDIDOS
            ('pedidos.ver', 'Ver Pedidos', 'pedidos', 'Permite visualizar pedidos'),
            ('pedidos.crear', 'Crear Pedidos', 'pedidos', 'Permite crear nuevas órdenes de pedido'),
            ('pedidos.editar_propio', 'Editar Pedidos Propios', 'pedidos', 'Permite editar sus propios pedidos'),
            ('pedidos.editar_todos', 'Editar Todos los Pedidos', 'pedidos', 'Permite editar cualquier pedido de la empresa'),
            ('pedidos.cancelar_propio', 'Cancelar Pedidos Propios', 'pedidos', 'Permite cancelar sus propios pedidos'),
            ('pedidos.cancelar_todos', 'Cancelar Todos los Pedidos', 'pedidos', 'Permite cancelar cualquier pedido de la empresa'),
            ('pedidos.aprobar_financiero', 'Aprobar Pedido (Financiero)', 'pedidos', 'Permite aprobar pedidos desde perspectiva financiera'),
            ('pedidos.aprobar_abastecimiento', 'Aprobar Pedido (Abastecimiento)', 'pedidos', 'Permite aprobar pedidos desde perspectiva de inventario'),

            # SOLICITUDES
            ('solicitudes.ver', 'Ver Solicitudes', 'solicitudes', 'Permite visualizar solicitudes'),
            ('solicitudes.crear', 'Crear Solicitudes', 'solicitudes', 'Permite crear nuevas solicitudes de productos'),
            ('solicitudes.editar_propio', 'Editar Solicitudes Propias', 'solicitudes', 'Permite editar sus propias solicitudes'),
            ('solicitudes.editar_todos', 'Editar Todas las Solicitudes', 'solicitudes', 'Permite editar cualquier solicitud de la empresa'),
            ('solicitudes.validar_financiero', 'Validar Solicitud (Financiero)', 'solicitudes', 'Permite validar solicitudes desde perspectiva financiera'),
            ('solicitudes.validar_abastecimiento', 'Validar Solicitud (Abastecimiento)', 'solicitudes', 'Permite validar solicitudes desde perspectiva de inventario'),
            ('solicitudes.aprobar', 'Aprobar Solicitudes', 'solicitudes', 'Permite aprobar solicitudes finalmente'),
            ('solicitudes.rechazar', 'Rechazar Solicitudes', 'solicitudes', 'Permite rechazar solicitudes'),

            # USUARIOS
            ('usuarios.ver', 'Ver Usuarios', 'usuarios', 'Permite visualizar usuarios de la empresa'),
            ('usuarios.crear', 'Crear Usuarios', 'usuarios', 'Permite crear nuevos usuarios'),
            ('usuarios.editar', 'Editar Usuarios', 'usuarios', 'Permite editar información de usuarios'),
            ('usuarios.activar_desactivar', 'Activar/Desactivar Usuarios', 'usuarios', 'Permite activar o desactivar cuentas de usuarios'),
            ('usuarios.asignar_roles', 'Asignar Roles', 'usuarios', 'Permite asignar y remover roles a usuarios'),
            ('usuarios.gestionar_grupos', 'Gestionar Grupos', 'usuarios', 'Permite asignar y remover grupos a usuarios'),

            # PRODUCTOS
            ('productos.ver', 'Ver Productos', 'productos', 'Permite visualizar el catálogo de productos'),
            ('productos.crear', 'Crear Productos', 'productos', 'Permite agregar nuevos productos al catálogo'),
            ('productos.editar', 'Editar Productos', 'productos', 'Permite modificar productos existentes'),
            ('productos.eliminar', 'Eliminar Productos', 'productos', 'Permite eliminar productos del catálogo'),
            ('productos.gestionar_categorias', 'Gestionar Categorías', 'productos', 'Permite crear y editar categorías de productos'),

            # INVENTARIO
            ('inventario.ver', 'Ver Inventario', 'inventario', 'Permite visualizar niveles de inventario'),
            ('inventario.ajustar', 'Ajustar Inventario', 'inventario', 'Permite realizar ajustes manuales de inventario'),
            ('inventario.ver_movimientos', 'Ver Movimientos', 'inventario', 'Permite ver historial de movimientos de inventario'),

            # REPORTES
            ('reportes.ver_financiero', 'Ver Reportes Financieros', 'reportes', 'Permite visualizar reportes financieros'),
            ('reportes.ver_inventario', 'Ver Reportes de Inventario', 'reportes', 'Permite visualizar reportes de inventario'),
            ('reportes.ver_pedidos', 'Ver Reportes de Pedidos', 'reportes', 'Permite visualizar reportes de pedidos'),
            ('reportes.ver_solicitudes', 'Ver Reportes de Solicitudes', 'reportes', 'Permite visualizar reportes de solicitudes'),
            ('reportes.exportar', 'Exportar Reportes', 'reportes', 'Permite exportar reportes a PDF/Excel'),

            # PAGOS
            ('pagos.ver', 'Ver Pagos', 'pagos', 'Permite visualizar información de pagos'),
            ('pagos.registrar', 'Registrar Pagos', 'pagos', 'Permite registrar pagos de pedidos'),
            ('pagos.validar', 'Validar Pagos', 'pagos', 'Permite validar pagos recibidos'),

            # EMPRESAS (Solo para Admin Sistema)
            ('empresas.ver', 'Ver Empresas', 'empresas', 'Permite visualizar empresas del sistema'),
            ('empresas.crear', 'Crear Empresas', 'empresas', 'Permite crear nuevas empresas'),
            ('empresas.editar', 'Editar Empresas', 'empresas', 'Permite editar información de empresas'),
            ('empresas.activar_desactivar', 'Activar/Desactivar Empresas', 'empresas', 'Permite activar o desactivar empresas'),
            ('empresas.gestionar_areas', 'Gestionar Áreas', 'empresas', 'Permite crear y editar áreas de la empresa'),
        ]

        permisos_creados = 0
        permisos_existentes = 0

        for codigo, nombre, modulo, descripcion in permisos_data:
            permiso, creado = Permiso.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'modulo': modulo,
                    'descripcion': descripcion
                }
            )

            if creado:
                permisos_creados += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Permiso creado: {codigo}'))
            else:
                permisos_existentes += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ Permisos inicializados:'))
        self.stdout.write(self.style.SUCCESS(f'   - Creados: {permisos_creados}'))
        self.stdout.write(self.style.SUCCESS(f'   - Ya existentes: {permisos_existentes}'))
        self.stdout.write(self.style.SUCCESS(f'   - Total: {permisos_creados + permisos_existentes}'))
