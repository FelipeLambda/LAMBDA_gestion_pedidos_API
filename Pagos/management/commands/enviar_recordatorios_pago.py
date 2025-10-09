from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import timedelta
from Pedidos.models import Pedido
from Pagos.models_notificaciones import NotificacionPago
from Usuarios.services.email_service import EmailService


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.stdout.write('\n=== SISTEMA DE RECORDATORIOS DE PAGO ===\n')

        hoy = timezone.now()
        email_service = EmailService()

        self.enviar_recordatorios_previos(hoy, email_service)
        self.enviar_recordatorios_mora(hoy, email_service)

        self.stdout.write(self.style.SUCCESS('\nProceso de recordatorios completado\n'))

    def enviar_recordatorios_previos(self, hoy, email_service):
        self.stdout.write('\n Buscando pagos próximos a vencer...')

        fecha_alerta = hoy + timedelta(days=3)

        pedidos = Pedido.objects.filter(
            estado=True,
            tipo_pago=Pedido.TiposPago.DIFERIDO,
            estado_pedido=Pedido.Estados.PENDIENTE_PAGO,
            fecha_limite_pago__date=fecha_alerta.date()
        ).select_related('empresa', 'solicitante')

        for pedido in pedidos:
            ya_notificado = NotificacionPago.objects.filter(
                pedido=pedido,
                tipo_notificacion=NotificacionPago.TiposNotificacion.RECORDATORIO_PREVIO,
                enviado_exitosamente=True
            ).exists()

            if ya_notificado:
                continue

            try:
                contexto = {
                    'titulo': 'Recordatorio de Pago Próximo a Vencer',
                    'empresa_nombre': pedido.empresa.nombre,
                    'numero_orden': pedido.numero_orden,
                    'fecha_limite': pedido.fecha_limite_pago.strftime('%d/%m/%Y'),
                    'monto_total': pedido.total,
                    'dias_restantes': 3,
                    'es_mora': False,
                    'mensaje_principal': f'Le recordamos que su pago con número de orden {pedido.numero_orden} vence en 3 días.',
                    'year': timezone.now().year
                }

                html_content = render_to_string('emails/recordatorio_pago.html', contexto)

                email_service.enviar_email(
                    destinatario=pedido.solicitante.email,
                    asunto=f'Recordatorio: Pago próximo a vencer - {pedido.numero_orden}',
                    html_content=html_content
                )

                NotificacionPago.objects.create(
                    pedido=pedido,
                    tipo_notificacion=NotificacionPago.TiposNotificacion.RECORDATORIO_PREVIO,
                    email_destinatario=pedido.solicitante.email,
                    enviado_exitosamente=True
                )

                self.stdout.write(
                    self.style.SUCCESS(f'Recordatorio previo enviado: {pedido.numero_orden}')
                )

            except Exception as e:
                NotificacionPago.objects.create(
                    pedido=pedido,
                    tipo_notificacion=NotificacionPago.TiposNotificacion.RECORDATORIO_PREVIO,
                    email_destinatario=pedido.solicitante.email,
                    enviado_exitosamente=False,
                    error_envio=str(e)
                )

                self.stdout.write(
                    self.style.ERROR(f'Error enviando recordatorio para {pedido.numero_orden}: {e}')
                )

    def enviar_recordatorios_mora(self, hoy, email_service):
        self.stdout.write('\n  Buscando pagos vencidos...')

        pedidos_vencidos = Pedido.objects.filter(
            estado=True,
            tipo_pago=Pedido.TiposPago.DIFERIDO,
            estado_pedido=Pedido.Estados.PENDIENTE_PAGO,
            fecha_limite_pago__lt=hoy
        ).select_related('empresa', 'solicitante')

        for pedido in pedidos_vencidos:
            dias_vencido = (hoy - pedido.fecha_limite_pago).days

            notificaciones_previas = NotificacionPago.objects.filter(
                pedido=pedido,
                tipo_notificacion__startswith='MORA',
                enviado_exitosamente=True
            ).count()

            tipo_notificacion = None
            debe_enviar = False

            T = NotificacionPago.TiposNotificacion
            if 1 <= dias_vencido <= 14 and notificaciones_previas == 0:
                debe_enviar = False
            elif 15 <= dias_vencido < 30 and notificaciones_previas == 0:
                tipo_notificacion = T.MORA_1
                debe_enviar = True
            elif 30 <= dias_vencido < 45 and notificaciones_previas == 1:
                tipo_notificacion = T.MORA_2
                debe_enviar = True
            elif 45 <= dias_vencido < 60 and notificaciones_previas == 2:
                tipo_notificacion = T.MORA_3
                debe_enviar = True
            elif 60 <= dias_vencido < 75 and notificaciones_previas == 3:
                tipo_notificacion = T.MORA_4
                debe_enviar = True
            elif dias_vencido >= 75 and notificaciones_previas == 4:
                tipo_notificacion = T.ACCION_LEGAL
                debe_enviar = True

            if not debe_enviar or not tipo_notificacion:
                continue

            try:
                numero_recordatorio = notificaciones_previas + 1

                contexto = {
                    'titulo': 'Notificación de Pago Vencido' if numero_recordatorio < 5 else 'NOTIFICACIÓN FINAL - Acciones Legales',
                    'empresa_nombre': pedido.empresa.nombre,
                    'numero_orden': pedido.numero_orden,
                    'fecha_limite': pedido.fecha_limite_pago.strftime('%d/%m/%Y'),
                    'monto_total': pedido.total,
                    'dias_vencidos': dias_vencido,
                    'es_mora': True,
                    'numero_recordatorio': numero_recordatorio,
                    'mensaje_principal': f'Su pago con número de orden {pedido.numero_orden} se encuentra vencido desde hace {dias_vencido} días.',
                    'year': timezone.now().year
                }

                html_content = render_to_string('emails/recordatorio_pago.html', contexto)

                asunto = f'MORA {numero_recordatorio}/5: Pago Vencido - {pedido.numero_orden}'
                if numero_recordatorio == 5:
                    asunto = f'URGENTE - ACCIONES LEGALES: Pago Vencido - {pedido.numero_orden}'

                email_service.enviar_email(
                    destinatario=pedido.solicitante.email,
                    asunto=asunto,
                    html_content=html_content
                )

                NotificacionPago.objects.create(
                    pedido=pedido,
                    tipo_notificacion=tipo_notificacion,
                    email_destinatario=pedido.solicitante.email,
                    enviado_exitosamente=True
                )

                self.stdout.write(
                    self.style.WARNING(f'Notificación de mora {numero_recordatorio}/5 enviada: {pedido.numero_orden}')
                )

            except Exception as e:
                NotificacionPago.objects.create(
                    pedido=pedido,
                    tipo_notificacion=tipo_notificacion,
                    email_destinatario=pedido.solicitante.email,
                    enviado_exitosamente=False,
                    error_envio=str(e)
                )

                self.stdout.write(
                    self.style.ERROR(f'Error enviando notificación de mora para {pedido.numero_orden}: {e}')
                )
