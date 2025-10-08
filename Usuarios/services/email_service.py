from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:

    @staticmethod
    def enviar_email_activacion(usuario, token):

        activation_url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"

        context = {
            'usuario': usuario,
            'activation_url': activation_url,
            'dias_expiracion': 7
        }

        html_message = render_to_string('emails/activacion_usuario.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Bienvenido a Lambda Commerce',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def enviar_email_activacion_empresa(empresa, token):
        """
        Envía email de activación a una empresa nueva.
        """
        activation_url = f"{settings.FRONTEND_URL}/activar-cuenta?token={token}"

        context = {
            'empresa': empresa,
            'activation_url': activation_url,
            'dias_expiracion': 7
        }

        html_message = render_to_string('emails/activacion_empresa.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Bienvenido a Lambda Commerce Solutions',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[empresa.correo_contacto],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def enviar_email_recuperacion_password(usuario, token):
        """
        Envía email de recuperación de contraseña.
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        context = {
            'usuario': usuario,
            'reset_url': reset_url
        }

        html_message = render_to_string('emails/recuperacion_password.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Recuperación de contraseña - Lambda Commerce',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            html_message=html_message,
            fail_silently=False,
        )
