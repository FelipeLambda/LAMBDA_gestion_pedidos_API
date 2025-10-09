from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from Pedidos.models import Pedido
from Pedidos.serializers import PedidoSerializer, AprobarPagoDiferidoSerializer
from LAMBDA_gestion_pedidos_API.utils import manejar_errores_db, requiere_grupos
from Usuarios.models import Grupos


class AprobarPagoDiferidoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    @manejar_errores_db
    def post(self, request, pk):
        """Aprueba o rechaza el pago diferido de un pedido (solo Admin Sistema)"""
        try:
            pedido = Pedido.objects.get(pk=pk, estado=True)

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
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

        except Pedido.DoesNotExist:
            return Response(
                {'error': 'Pedido no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class ListarPedidosPagoDiferidoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @requiere_grupos(Grupos.ADMIN_SISTEMA)
    def get(self, request):
        pedidos = Pedido.objects.filter(
            estado=True,
            tipo_pago='DIFERIDO',
            pago_diferido_aprobado=False
        ).select_related('empresa', 'solicitante')

        serializer = PedidoSerializer(pedidos, many=True)
        return Response({
            'total': pedidos.count(),
            'pedidos': serializer.data
        }, status=status.HTTP_200_OK)
