from django.core.management.base import BaseCommand
from Usuarios.models import Permiso, Role, Grupos


class Command(BaseCommand):
    help = 'Inicializa los roles del sistema con sus permisos RBAC'

    ROLES_SISTEMA = {
        Grupos.ADMIN_SISTEMA: {
            'descripcion': 'Administrador global de LAMBDA con acceso total',
            'permisos': '*'
        },
        Grupos.ADMIN_EMPRESA: {
            'descripcion': 'Administrador de empresa con gestión completa de su organización',
            'permisos': [
                'empresas.listar', 'empresas.ver',
                'areas.crear', 'areas.editar', 'areas.eliminar', 'areas.listar',
                'usuarios.crear', 'usuarios.editar', 'usuarios.listar', 'usuarios.ver',
                'usuarios.activar_desactivar', 'usuarios.regenerar_token',
                'usuarios.asignar_roles', 'usuarios.remover_roles',
                'roles.crear', 'roles.editar', 'roles.eliminar',
                'productos.listar', 'productos.ver',
                'inventario.ver_stock',
                'solicitudes.crear', 'solicitudes.listar', 'solicitudes.ver', 'solicitudes.eliminar',
                'pedidos.crear_desde_solicitud', 'pedidos.listar', 'pedidos.ver',
                'pedidos.editar', 'pedidos.eliminar', 'pedidos.actualizar_estado',
                'pedidos.descargar_factura', 'pedidos.reenviar_factura',
                'pagos.registrar', 'pagos.listar', 'pagos.ver', 'pagos.exportar',
                'reportes.exportar_pedidos', 'reportes.exportar_facturacion',
                'reportes.exportar_pagos', 'reportes.exportar_consolidado_financiero',
                'reportes.exportar_solicitudes', 'reportes.exportar_inventario',
                'reportes.exportar_stock', 'reportes.exportar_excel',
                'reportes.exportar_pdf', 'reportes.exportar_csv',
                'reportes.ver_dashboard_financiero', 'reportes.comparar_periodos',
            ]
        },
        Grupos.JEFE_AREA: {
            'descripcion': 'Jefe de área que gestiona usuarios y solicitudes de su área',
            'permisos': [
                'usuarios.editar', 'usuarios.listar', 'usuarios.ver',
                'productos.listar', 'productos.ver',
                'solicitudes.listar', 'solicitudes.ver',
                'pedidos.listar', 'pedidos.ver',
            ]
        },
        Grupos.VALIDADOR_FINANCIERO: {
            'descripcion': 'Validador de solicitudes desde perspectiva financiera',
            'permisos': [
                'productos.listar', 'productos.ver',
                'solicitudes.listar', 'solicitudes.ver',
                'solicitudes.validar_financiero', 'solicitudes.rechazar_financiero',
                'pedidos.listar', 'pedidos.ver',
                'pagos.listar', 'pagos.ver',
                'reportes.exportar_pedidos', 'reportes.exportar_facturacion',
                'reportes.exportar_pagos', 'reportes.exportar_consolidado_financiero',
                'reportes.exportar_solicitudes',
            ]
        },
        Grupos.VALIDADOR_ABASTECIMIENTO: {
            'descripcion': 'Validador de solicitudes desde perspectiva de inventario',
            'permisos': [
                'productos.listar', 'productos.ver',
                'inventario.ver_stock',
                'solicitudes.listar', 'solicitudes.ver',
                'solicitudes.validar_abastecimiento', 'solicitudes.modificar_abastecimiento',
                'solicitudes.aprobar_abastecimiento', 'solicitudes.rechazar_abastecimiento',
                'pedidos.listar', 'pedidos.ver',
                'reportes.exportar_solicitudes', 'reportes.exportar_inventario',
                'reportes.exportar_stock',
            ]
        },
        Grupos.SOLICITANTE: {
            'descripcion': 'Usuario base que crea solicitudes de productos',
            'permisos': [
                'productos.listar', 'productos.ver',
                'inventario.ver_stock',
                'solicitudes.crear', 'solicitudes.listar', 'solicitudes.ver',
                'pedidos.listar', 'pedidos.ver',
            ]
        },
    }

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🔧 Inicializando roles del sistema RBAC...\n'))

        roles_creados = 0
        roles_actualizados = 0

        for nombre_rol, config in self.ROLES_SISTEMA.items():
            rol, creado = Role.objects.get_or_create(
                nombre=nombre_rol,
                empresa=None,
                defaults={
                    'descripcion': config['descripcion'],
                    'tipo': 'SISTEMA',
                    'es_modificable': False
                }
            )

            if not creado:
                rol.descripcion = config['descripcion']
                rol.save()

            if config['permisos'] == '*':
                todos_permisos = Permiso.objects.all()
                rol.permisos.set(todos_permisos)
                permisos_count = todos_permisos.count()
                msg = f'  ✓ {nombre_rol}: TODOS los permisos ({permisos_count})'
            else:
                permisos = Permiso.objects.filter(codigo__in=config['permisos'])
                rol.permisos.set(permisos)
                permisos_count = permisos.count()
                esperados = len(config['permisos'])
                msg = f'  ✓ {nombre_rol}: {permisos_count}/{esperados} permisos'

            self.stdout.write(self.style.SUCCESS(msg) if creado else self.style.WARNING(msg))

            if creado:
                roles_creados += 1
            else:
                roles_actualizados += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ Roles del sistema inicializados:'))
        self.stdout.write(f'   - Creados: {roles_creados}')
        self.stdout.write(f'   - Actualizados: {roles_actualizados}')
        self.stdout.write(f'   - Total: {len(self.ROLES_SISTEMA)}')
