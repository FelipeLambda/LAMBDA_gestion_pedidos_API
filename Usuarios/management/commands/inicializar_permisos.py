from django.core.management.base import BaseCommand
from Usuarios.models import Permiso


class Command(BaseCommand):
    help = 'Inicializa los 83 permisos del sistema RBAC'

    PERMISOS = [
        # EMPRESAS (10)
        ('empresas.crear', 'Crear Empresas', 'empresas', 'Solo ADMIN_SISTEMA'),
        ('empresas.editar', 'Editar Empresas', 'empresas', 'Solo ADMIN_SISTEMA'),
        ('empresas.listar', 'Listar Empresas', 'empresas', 'ADMIN_SISTEMA, ADMIN_EMPRESA'),
        ('empresas.ver', 'Ver Empresas', 'empresas', 'ADMIN_SISTEMA, ADMIN_EMPRESA'),
        ('empresas.activar', 'Activar Empresa', 'empresas', 'Público con token'),
        ('empresas.regenerar_token', 'Regenerar Token Empresa', 'empresas', 'Solo ADMIN_SISTEMA'),
        ('areas.crear', 'Crear Áreas', 'empresas', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('areas.editar', 'Editar Áreas', 'empresas', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('areas.eliminar', 'Eliminar Áreas', 'empresas', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('areas.listar', 'Listar Áreas', 'empresas', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),

        # USUARIOS (15)
        ('usuarios.crear', 'Crear Usuarios', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('usuarios.editar', 'Editar Usuarios', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA, JEFE_AREA'),
        ('usuarios.listar', 'Listar Usuarios', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA, JEFE_AREA'),
        ('usuarios.ver', 'Ver Usuarios', 'usuarios', 'Todos autenticados'),
        ('usuarios.activar_desactivar', 'Activar/Desactivar Usuarios', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('usuarios.regenerar_token', 'Regenerar Token Usuario', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('usuarios.asignar_roles', 'Asignar Roles', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('usuarios.remover_roles', 'Remover Roles', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('usuarios.cambiar_password_propio', 'Cambiar Password Propio', 'usuarios', 'Usuario autenticado'),
        ('usuarios.recuperar_password', 'Recuperar Password', 'usuarios', 'Público'),
        ('usuarios.ver_perfil_propio', 'Ver Perfil Propio', 'usuarios', 'Usuario autenticado'),
        ('usuarios.editar_perfil_propio', 'Editar Perfil Propio', 'usuarios', 'Usuario autenticado'),
        ('roles.crear', 'Crear Roles', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('roles.editar', 'Editar Roles', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('roles.eliminar', 'Eliminar Roles', 'usuarios', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),

        # PRODUCTOS (9)
        ('productos.crear', 'Crear Productos', 'productos', 'Solo ADMIN_SISTEMA'),
        ('productos.editar', 'Editar Productos', 'productos', 'Solo ADMIN_SISTEMA'),
        ('productos.eliminar', 'Eliminar Productos', 'productos', 'Solo ADMIN_SISTEMA'),
        ('productos.listar', 'Listar Productos', 'productos', 'Todos autenticados'),
        ('productos.ver', 'Ver Productos', 'productos', 'Todos autenticados'),
        ('categorias.crear', 'Crear Categorías', 'productos', 'Solo ADMIN_SISTEMA'),
        ('categorias.editar', 'Editar Categorías', 'productos', 'Solo ADMIN_SISTEMA'),
        ('categorias.eliminar', 'Eliminar Categorías', 'productos', 'Solo ADMIN_SISTEMA'),
        ('productos.ver_alertas_stock', 'Ver Alertas Stock', 'productos', 'Solo ADMIN_SISTEMA'),

        # INVENTARIO (6)
        ('inventario.listar_movimientos', 'Listar Movimientos', 'inventario', 'Solo ADMIN_SISTEMA'),
        ('inventario.registrar_movimiento', 'Registrar Movimiento', 'inventario', 'Solo ADMIN_SISTEMA'),
        ('inventario.ver_stock', 'Ver Stock', 'inventario', 'Todos autenticados'),
        ('inventario.reservar_stock', 'Reservar Stock', 'inventario', 'Sistema automático'),
        ('inventario.liberar_stock', 'Liberar Stock', 'inventario', 'Sistema automático'),
        ('inventario.exportar', 'Exportar Inventario', 'inventario', 'Solo ADMIN_SISTEMA'),

        # SOLICITUDES (10)
        ('solicitudes.crear', 'Crear Solicitudes', 'solicitudes', 'SOLICITANTE, ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('solicitudes.listar', 'Listar Solicitudes', 'solicitudes', 'Todos autenticados con filtro'),
        ('solicitudes.ver', 'Ver Solicitudes', 'solicitudes', 'Solicitante, ADMIN_EMPRESA, VALIDADORES, ADMIN_SISTEMA'),
        ('solicitudes.eliminar', 'Eliminar Solicitudes', 'solicitudes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('solicitudes.validar_abastecimiento', 'Validar Abastecimiento', 'solicitudes', 'VALIDADOR_ABASTECIMIENTO, ADMIN_SISTEMA'),
        ('solicitudes.modificar_abastecimiento', 'Modificar Abastecimiento', 'solicitudes', 'VALIDADOR_ABASTECIMIENTO, ADMIN_SISTEMA'),
        ('solicitudes.aprobar_abastecimiento', 'Aprobar Abastecimiento', 'solicitudes', 'VALIDADOR_ABASTECIMIENTO, ADMIN_SISTEMA'),
        ('solicitudes.rechazar_abastecimiento', 'Rechazar Abastecimiento', 'solicitudes', 'VALIDADOR_ABASTECIMIENTO, ADMIN_SISTEMA'),
        ('solicitudes.validar_financiero', 'Validar Financiero', 'solicitudes', 'VALIDADOR_FINANCIERO, ADMIN_SISTEMA'),
        ('solicitudes.rechazar_financiero', 'Rechazar Financiero', 'solicitudes', 'VALIDADOR_FINANCIERO, ADMIN_SISTEMA'),

        # PEDIDOS (14)
        ('pedidos.crear_desde_solicitud', 'Crear Pedido desde Solicitud', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.listar', 'Listar Pedidos', 'pedidos', 'Todos autenticados con filtro'),
        ('pedidos.ver', 'Ver Pedidos', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA, Solicitante'),
        ('pedidos.editar', 'Editar Pedidos', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.eliminar', 'Eliminar Pedidos', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.actualizar_estado', 'Actualizar Estado Pedido', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.aprobar_pago_diferido', 'Aprobar Pago Diferido', 'pedidos', 'Solo ADMIN_SISTEMA'),
        ('pedidos.rechazar_pago_diferido', 'Rechazar Pago Diferido', 'pedidos', 'Solo ADMIN_SISTEMA'),
        ('pedidos.listar_pago_diferido_pendiente', 'Listar Pagos Diferidos Pendientes', 'pedidos', 'Solo ADMIN_SISTEMA'),
        ('pedidos.descargar_factura', 'Descargar Factura', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.reenviar_factura', 'Reenviar Factura', 'pedidos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pedidos.validar_pago', 'Validar Pago', 'pedidos', 'Solo ADMIN_SISTEMA'),
        ('pedidos.enviar_recordatorios', 'Enviar Recordatorios', 'pedidos', 'Sistema automático'),
        ('pedidos.gestionar_mora', 'Gestionar Mora', 'pedidos', 'Sistema automático'),

        # PAGOS (7)
        ('pagos.registrar', 'Registrar Pago', 'pagos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pagos.listar', 'Listar Pagos', 'pagos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pagos.ver', 'Ver Pagos', 'pagos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('pagos.validar', 'Validar Pago', 'pagos', 'Solo ADMIN_SISTEMA'),
        ('pagos.aprobar', 'Aprobar Pago', 'pagos', 'Solo ADMIN_SISTEMA'),
        ('pagos.rechazar', 'Rechazar Pago', 'pagos', 'Solo ADMIN_SISTEMA'),
        ('pagos.exportar', 'Exportar Pagos', 'pagos', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),

        # REPORTES (12)
        ('reportes.exportar_pedidos', 'Exportar Pedidos', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_facturacion', 'Exportar Facturación', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_pagos', 'Exportar Pagos', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_consolidado_financiero', 'Exportar Consolidado Financiero', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_solicitudes', 'Exportar Solicitudes', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_inventario', 'Exportar Inventario', 'reportes', 'Solo ADMIN_SISTEMA'),
        ('reportes.exportar_stock', 'Exportar Stock', 'reportes', 'Solo ADMIN_SISTEMA'),
        ('reportes.exportar_excel', 'Exportar Excel', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_pdf', 'Exportar PDF', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.exportar_csv', 'Exportar CSV', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.ver_dashboard_financiero', 'Ver Dashboard Financiero', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
        ('reportes.comparar_periodos', 'Comparar Periodos', 'reportes', 'ADMIN_EMPRESA, ADMIN_SISTEMA'),
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🔧 Inicializando permisos del sistema RBAC...\n'))

        creados = 0
        actualizados = 0

        for codigo, nombre, modulo, descripcion in self.PERMISOS:
            permiso, creado = Permiso.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'modulo': modulo,
                    'descripcion': descripcion
                }
            )

            if creado:
                creados += 1
                self.stdout.write(f'  ✓ Creado: {codigo}')
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ Permisos inicializados:'))
        self.stdout.write(f'   - Creados: {creados}')
        self.stdout.write(f'   - Actualizados: {actualizados}')
        self.stdout.write(f'   - Total: {len(self.PERMISOS)}')
