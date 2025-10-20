from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pedidos.models import Pedido, DetallePedido
from Pedidos.serializers import (
    PedidoSerializer,
    CrearPedidoSerializer,
    ActualizarEstadoPedidoSerializer,
    EditarPedidoSerializer
)
from Solicitudes.models import Solicitud
from Inventario.models import MovimientoInventario
from Usuarios.models import Grupos
from Usuarios.services.email_service import EmailService
from Reportes.utils_pdf import FacturaPDFGenerator
from LAMBDA_gestion_pedidos_API.utils import (
    FiltradoEmpresaMixin,
    PermisosPorEmpresaMixin,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    manejar_errores_db,
    requiere_permisos
)


class PedidoListAPIView(FiltradoEmpresaMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pedidos = Pedido.objects.all()
        elif usuario.roles.filter(nombre=Grupos.ADMIN_EMPRESA).exists():
            pedidos = self.filtrar_por_empresa(request, Pedido.objects.all())
        else:
            pedidos = Pedido.objects.filter(solicitante=usuario)

        serializer = PedidoSerializer(pedidos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PedidoDetailAPIView(FiltradoEmpresaMixin, PermisosPorEmpresaMixin, ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @manejar_errores_db
    def get(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        puede_ver, mensaje_error = self.puede_ver_recurso(request.user, pedido)
        if not puede_ver:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        serializer = PedidoSerializer(pedido)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @requiere_permisos('pedidos.eliminar')
    @manejar_errores_db
    def delete(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        if pedido.estado_pedido not in [Pedido.Estados.PENDIENTE_PAGO, Pedido.Estados.PAGO_CONFIRMADO]:
            return Response(
                {'error': 'Solo se pueden eliminar pedidos en estado PENDIENTE_PAGO o PAGO_CONFIRMADO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        puede_eliminar, mensaje_error = self.puede_eliminar_recurso(request.user, pedido)
        if not puede_eliminar:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        # Liberar reservas de stock antes de eliminar pedido
        if pedido.estado_pedido == Pedido.Estados.PENDIENTE_PAGO:
            for detalle in pedido.detalles.filter(estado=True):
                MovimientoInventario.objects.create(
                    tipo_movimiento=MovimientoInventario.TiposMovimiento.LIBERACION_RESERVA,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    usuario_responsable=request.user,
                    pedido=pedido,
                    observaciones=f'Liberación por eliminación de pedido - {pedido.numero_orden}'
                )

        pedido.soft_delete()

        return Response(
            {'mensaje': 'Pedido eliminado exitosamente. Reservas liberadas.'},
            status=status.HTTP_200_OK
        )


class CrearPedidoDesdeSolicitudAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.crear')
    @manejar_errores_db
    def post(self, request):
        serializer = CrearPedidoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        solicitud_id = serializer.validated_data['solicitud_id']
        observaciones = serializer.validated_data.get('observaciones', '')

        solicitud, error = self.obtener_objeto_o_404(Solicitud, solicitud_id, mensaje_error='Solicitud no encontrada')
        if error:
            return error

        if solicitud.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes crear pedidos desde solicitudes de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not solicitud.empresa.tiene_areas_criticas():
            return Response({
                'error': 'La empresa debe tener configuradas las áreas financiera y de abastecimiento antes de crear pedidos.'
            }, status=status.HTTP_400_BAD_REQUEST)

        detalles_solicitud = solicitud.detalles.filter(estado=True)
        for detalle in detalles_solicitud:
            if detalle.cantidad <= 0:
                return Response({
                    'error': f'La cantidad debe ser mayor a 0 para {detalle.producto.nombre}'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not detalle.producto.tiene_stock_suficiente(detalle.cantidad):
                return Response({
                    'error': f'Stock insuficiente para {detalle.producto.nombre}. Disponible: {detalle.producto.stock_disponible_real}, Solicitado: {detalle.cantidad}'
                }, status=status.HTTP_400_BAD_REQUEST)

        numero_orden = f"PED-{solicitud.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        pedido = Pedido.objects.create(
            solicitud=solicitud,
            empresa=solicitud.empresa,
            solicitante=solicitud.solicitante,
            numero_orden=numero_orden,
            observaciones=observaciones
        )

        for detalle_solicitud in detalles_solicitud:
            DetallePedido.objects.create(
                pedido=pedido,
                producto=detalle_solicitud.producto,
                cantidad=detalle_solicitud.cantidad,
                precio_unitario=detalle_solicitud.precio_unitario
            )

            MovimientoInventario.objects.create(
                tipo_movimiento=MovimientoInventario.TiposMovimiento.RESERVA,
                producto=detalle_solicitud.producto,
                cantidad=detalle_solicitud.cantidad,
                usuario_responsable=request.user,
                pedido=pedido,
                observaciones=f'Reserva automática para pedido {pedido.numero_orden}'
            )

        return Response({
            'mensaje': 'Pedido creado exitosamente. Stock reservado.',
            'pedido': PedidoSerializer(pedido).data
        }, status=status.HTTP_201_CREATED)


class ActualizarEstadoPedidoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.actualizar_estado')
    @manejar_errores_db
    def patch(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        if pedido.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes actualizar pedidos de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ActualizarEstadoPedidoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        nuevo_estado = serializer.validated_data['estado_pedido']
        observaciones = serializer.validated_data.get('observaciones', pedido.observaciones)
        estado_anterior = pedido.estado_pedido

        pedido.estado_pedido = nuevo_estado
        pedido.observaciones = observaciones

        if nuevo_estado == Pedido.Estados.COMPLETADO:
            pedido.fecha_completado = timezone.now()

        # Al confirmar pago: liberar reserva y descontar stock disponible
        if nuevo_estado == Pedido.Estados.PAGO_CONFIRMADO and estado_anterior == Pedido.Estados.PENDIENTE_PAGO:
            for detalle in pedido.detalles.filter(estado=True):
                MovimientoInventario.objects.create(
                    tipo_movimiento=MovimientoInventario.TiposMovimiento.LIBERACION_RESERVA,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    usuario_responsable=request.user,
                    pedido=pedido,
                    observaciones=f'Liberación de reserva por pago confirmado - {pedido.numero_orden}'
                )

                detalle.producto.stock_disponible -= detalle.cantidad
                detalle.producto.save()

                MovimientoInventario.objects.create(
                    tipo_movimiento=MovimientoInventario.TiposMovimiento.SALIDA,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    usuario_responsable=request.user,
                    observaciones=f'Salida por pedido confirmado - {pedido.numero_orden}'
                )

            pedido.save()
            generator = FacturaPDFGenerator(pedido)
            pdf_bytes = generator.generar(como_respuesta=False)
            EmailService.enviar_factura_pdf(pedido, pdf_bytes)
            pedido.factura_enviada = True

        # Al cancelar pedido pendiente de pago: liberar reservas de stock
        if nuevo_estado == Pedido.Estados.CANCELADO and estado_anterior == Pedido.Estados.PENDIENTE_PAGO:
            for detalle in pedido.detalles.filter(estado=True):
                MovimientoInventario.objects.create(
                    tipo_movimiento=MovimientoInventario.TiposMovimiento.LIBERACION_RESERVA,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    usuario_responsable=request.user,
                    pedido=pedido,
                    observaciones=f'Liberación de reserva por cancelación - {pedido.numero_orden}'
                )

        pedido.save()

        return Response({
            'mensaje': 'Estado de pedido actualizado exitosamente',
            'pedido': PedidoSerializer(pedido).data
        }, status=status.HTTP_200_OK)


class EditarPedidoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.editar')
    @manejar_errores_db
    def patch(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        if pedido.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes editar pedidos de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not pedido.puede_editarse:
            return Response(
                {'error': 'Solo se pueden editar pedidos en estado PENDIENTE_PAGO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EditarPedidoSerializer(pedido, data=request.data, partial=True)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        pedido = serializer.save()

        return Response({
            'mensaje': 'Pedido actualizado exitosamente',
            'pedido': PedidoSerializer(pedido).data
        }, status=status.HTTP_200_OK)

class DescargarFacturaPDFAPIView(FiltradoEmpresaMixin, PermisosPorEmpresaMixin, ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        puede_ver, mensaje_error = self.puede_ver_recurso(request.user, pedido)
        if not puede_ver:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        if pedido.estado_pedido not in [Pedido.Estados.PAGO_CONFIRMADO, Pedido.Estados.EN_DESPACHO, Pedido.Estados.COMPLETADO]:
            return Response(
                {'error': 'Solo se puede descargar factura de pedidos con pago confirmado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        generator = FacturaPDFGenerator(pedido)
        return generator.generar(como_respuesta=True)


class ReenviarFacturaAPIView(FiltradoEmpresaMixin, PermisosPorEmpresaMixin, ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.reenviar_factura')
    @manejar_errores_db
    def post(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        puede_ver, mensaje_error = self.puede_ver_recurso(request.user, pedido)
        if not puede_ver:
            return Response({'error': mensaje_error}, status=status.HTTP_403_FORBIDDEN)

        if pedido.estado_pedido not in [Pedido.Estados.PAGO_CONFIRMADO, Pedido.Estados.EN_DESPACHO, Pedido.Estados.COMPLETADO]:
            return Response(
                {'error': 'Solo se puede enviar factura de pedidos con pago confirmado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        generator = FacturaPDFGenerator(pedido)
        pdf_bytes = generator.generar(como_respuesta=False)
        EmailService.enviar_factura_pdf(pedido, pdf_bytes)

        pedido.factura_enviada = True
        pedido.save()

        return Response({
            'mensaje': 'Factura reenviada exitosamente'
        }, status=status.HTTP_200_OK)
