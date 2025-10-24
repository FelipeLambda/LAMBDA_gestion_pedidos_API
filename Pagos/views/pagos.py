from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pagos.models import Pago
from Pagos.serializers import (
    PagoSerializer,
    RegistrarPagoSerializer,
    ValidarPagoSerializer
)
from Pedidos.models import Pedido
from Pagos.models import Pago
from LAMBDA_gestion_pedidos_API.utils import (
    manejar_errores_db,
    requiere_permisos,
    ObjetoDetailMixin,
    SerializerValidationMixin,
    PaginacionMixin
)
from Usuarios.models import Grupos


class RegistrarPagoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pagos.registrar')
    @manejar_errores_db
    def post(self, request):
        serializer = RegistrarPagoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        pedido_id = serializer.validated_data['pedido_id']
        monto = serializer.validated_data['monto']
        metodo_pago = serializer.validated_data['metodo_pago']
        referencia_pago = serializer.validated_data.get('referencia_pago', '')
        fecha_pago = serializer.validated_data['fecha_pago']
        observaciones = serializer.validated_data.get('observaciones', '')

        pedido, error = self.obtener_objeto_o_404(Pedido, pedido_id)
        if error:
            return error

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            if pedido.empresa != usuario.empresa:
                return Response(
                    {'error': 'No tiene permisos para registrar pagos de otras empresas'},
                    status=status.HTTP_403_FORBIDDEN
                )

        total_pagado = pedido.pagos.filter(
            estado=True,
            estado_pago__in=[Pago.Estados.COMPLETADO, Pago.Estados.PARCIAL]
        ).aggregate(total=Pago.objects.model.Sum('monto'))['total'] or 0

        monto_pendiente = pedido.total - total_pagado

        if abs(monto - monto_pendiente) < 0.01:
            estado_pago = Pago.Estados.COMPLETADO
        elif monto < monto_pendiente:
            estado_pago = Pago.Estados.PARCIAL
        else:
            estado_pago = Pago.Estados.PENDIENTE

        pago = Pago.objects.create(
            pedido=pedido,
            monto=monto,
            estado_pago=estado_pago,
            metodo_pago=metodo_pago,
            referencia_pago=referencia_pago,
            fecha_pago=fecha_pago,
            observaciones=observaciones
        )

        return Response({
            'mensaje': 'Pago registrado exitosamente',
            'pago': PagoSerializer(pago).data
        }, status=status.HTTP_201_CREATED)


class ListarPagosAPIView(PaginacionMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pagos.listar')
    def get(self, request):
        usuario = request.user

        if usuario.is_superuser or usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pagos = Pago.objects.all().select_related('pedido', 'validado_por')
        else:
            pagos = Pago.objects.filter(
                pedido__empresa=usuario.empresa
            ).select_related('pedido', 'validado_por')

        pedido_id = request.query_params.get('pedido_id')
        if pedido_id:
            pagos = pagos.filter(pedido_id=pedido_id)

        estado_pago = request.query_params.get('estado')
        if estado_pago:
            pagos = pagos.filter(estado_pago=estado_pago)

        pagos = pagos.filter(estado=True).order_by('-fecha_creacion')

        pagos_paginados = self.paginar_queryset(pagos, request)
        serializer = PagoSerializer(pagos_paginados, many=True)
        return self.get_paginated_response(serializer)


class PagoDetailAPIView(ObjetoDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pagos.ver')
    def get(self, request, pk):
        pago, error = self.obtener_objeto_o_404(Pago, pk)
        if error:
            return error

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            if pago.pedido.empresa != usuario.empresa:
                return Response(
                    {'error': 'No tiene permisos para ver pagos de otras empresas'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = PagoSerializer(pago)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ValidarPagoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pagos.validar')
    @manejar_errores_db
    def patch(self, request, pk):
        pago, error = self.obtener_objeto_o_404(Pago, pk)
        if error:
            return error

        if pago.pedido.empresa != request.user.empresa and not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo puedes validar pagos de tu empresa'},
                status=status.HTTP_403_FORBIDDEN
            )

        if pago.estado_pago in [Pago.Estados.COMPLETADO, Pago.Estados.RECHAZADO]:
            return Response(
                {'error': 'Este pago ya fue validado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ValidarPagoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        nuevo_estado = serializer.validated_data['estado_pago']
        observaciones_adicionales = serializer.validated_data.get('observaciones', '')

        pago.estado_pago = nuevo_estado
        pago.validado_por = request.user

        if observaciones_adicionales:
            pago.observaciones = f"{pago.observaciones or ''}\n\n{observaciones_adicionales}"

        pago.save()

        if nuevo_estado == Pago.Estados.COMPLETADO:
            pedido = pago.pedido
            total_pagado = pedido.pagos.filter(
                estado=True,
                estado_pago=Pago.Estados.COMPLETADO
            ).aggregate(total=Pago.objects.model.Sum('monto'))['total'] or 0

            if abs(total_pagado - pedido.total) < 0.01:
                if pedido.estado_pedido == Pedido.Estados.PENDIENTE_PAGO:
                    pedido.estado_pedido = Pedido.Estados.PAGO_CONFIRMADO
                    pedido.save()

        return Response({
            'mensaje': f'Pago {nuevo_estado.lower()} exitosamente',
            'pago': PagoSerializer(pago).data
        }, status=status.HTTP_200_OK)
