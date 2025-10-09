from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


class EmailService:

    @classmethod
    def _enviar_desde_template(cls, template_name, context, destinatario, asunto):
        mensaje = render_to_string(f'emails/{template_name}', context)
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )

    @classmethod
    def enviar_email_activacion(cls, usuario, token):
        url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"
        cls._enviar_desde_template(
            template_name='activacion_usuario.txt',
            context={'usuario': usuario, 'url': url},
            destinatario=usuario.email,
            asunto='Bienvenido a Lambda Commerce'
        )

    @classmethod
    def enviar_email_activacion_empresa(cls, empresa, token):
        url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"
        cls._enviar_desde_template(
            template_name='activacion_empresa.txt',
            context={'empresa': empresa, 'url': url},
            destinatario=empresa.correo_contacto,
            asunto='Bienvenido a Lambda Commerce Solutions'
        )

    @classmethod
    def enviar_email_recuperacion_password(cls, usuario, token):
        url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        cls._enviar_desde_template(
            template_name='recuperacion_password.txt',
            context={'usuario': usuario, 'url': url},
            destinatario=usuario.email,
            asunto='Recuperación de contraseña - Lambda Commerce'
        )

    @classmethod
    def enviar_recordatorio_pago_previo(cls, pedido):
        cls._enviar_desde_template(
            template_name='recordatorio_pago_previo.txt',
            context={
                'pedido': pedido,
                'fecha_limite': pedido.fecha_limite_pago.strftime('%d/%m/%Y')
            },
            destinatario=pedido.solicitante.email,
            asunto=f'Recordatorio: Pago próximo a vencer - {pedido.numero_orden}'
        )

    @classmethod
    def enviar_notificacion_mora(cls, pedido, dias_vencido, numero_recordatorio):
        es_accion_legal = numero_recordatorio == 5

        template_name = 'notificacion_mora_legal.txt' if es_accion_legal else 'notificacion_mora.txt'
        asunto = (
            f'URGENTE - ACCIONES LEGALES: Pago Vencido - {pedido.numero_orden}'
            if es_accion_legal
            else f'MORA {numero_recordatorio}/5: Pago Vencido - {pedido.numero_orden}'
        )

        cls._enviar_desde_template(
            template_name=template_name,
            context={
                'pedido': pedido,
                'dias_vencido': dias_vencido,
                'numero_recordatorio': numero_recordatorio,
                'fecha_limite': pedido.fecha_limite_pago.strftime('%d/%m/%Y')
            },
            destinatario=pedido.solicitante.email,
            asunto=asunto
        )
