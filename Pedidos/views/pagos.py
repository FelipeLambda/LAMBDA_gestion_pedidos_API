from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pedidos.models import Pedido
from Pedidos.serializers import PedidoSerializer, AprobarPagoDiferidoSerializer
from LAMBDA_gestion_pedidos_API.utils import (
    manejar_errores_db,
    requiere_permisos,
    ObjetoDetailMixin,
    SerializerValidationMixin
)
from Usuarios.models import Grupos


class AprobarPagoDiferidoAPIView(ObjetoDetailMixin, SerializerValidationMixin, APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.aprobar_pago_diferido')
    @manejar_errores_db
    def post(self, request, pk):
        pedido, error = self.obtener_objeto_o_404(Pedido, pk)
        if error:
            return error

        if not request.user.is_superuser and not request.user.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            return Response(
                {'error': 'Solo Admin Sistema puede aprobar pagos diferidos'},
                status=status.HTTP_403_FORBIDDEN
            )

        if pedido.tipo_pago != 'DIFERIDO':
            return Response(
                {'error': 'Este pedido no es de pago diferido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if pedido.pago_diferido_aprobado:
            return Response(
                {'error': 'Este pedido ya tiene el pago diferido aprobado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AprobarPagoDiferidoSerializer(data=request.data)
        es_valido, error = self.validar_serializer(serializer)
        if not es_valido:
            return error

        aprobado = serializer.validated_data['aprobado']
        observaciones_adicionales = serializer.validated_data.get('observaciones', '')

        if aprobado:
            pedido.pago_diferido_aprobado = True
            pedido.aprobador_pago_diferido = request.user
            pedido.fecha_aprobacion_pago_diferido = timezone.now()
            mensaje = 'Pago diferido aprobado exitosamente'
        else:
            pedido.tipo_pago = 'INMEDIATO'
            pedido.fecha_limite_pago = None
            pedido.observaciones = f"{pedido.observaciones or ''}\n\nPago diferido rechazado: {observaciones_adicionales}"
            mensaje = 'Pago diferido rechazado. Pedido cambiado a pago inmediato.'

        pedido.save()

        return Response({
            'mensaje': mensaje,
            'pedido': PedidoSerializer(pedido).data
        }, status=status.HTTP_200_OK)


class ListarPedidosPagoDiferidoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_permisos('pedidos.listar_pagos_diferidos')
    def get(self, request):
        pedidos = Pedido.objects.filter(
            estado=True,
            tipo_pago='DIFERIDO',
            pago_diferido_aprobado=False
        ).select_related('empresa', 'solicitante')

        usuario = request.user
        if not usuario.is_superuser and not usuario.roles.filter(nombre=Grupos.ADMIN_SISTEMA).exists():
            pedidos = pedidos.filter(empresa=usuario.empresa)

        serializer = PedidoSerializer(pedidos, many=True)
        return Response({
            'total': pedidos.count(),
            'pedidos': serializer.data
        }, status=status.HTTP_200_OK)
