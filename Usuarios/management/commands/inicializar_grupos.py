from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from Usuarios.models import Grupos


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        grupos = [
            Grupos.ADMIN_SISTEMA,
            Grupos.ADMIN_EMPRESA,
            Grupos.VALIDADOR_FINANCIERO,
            Grupos.VALIDADOR_ABASTECIMIENTO,
            Grupos.SOLICITANTE,
        ]

        self.stdout.write(self.style.WARNING('\n=== GRUPOS PREDEFINIDOS DEL SISTEMA ==='))
        self.stdout.write('Los grupos son estándar para garantizar seguridad, compliance y flujos uniformes.')
        self.stdout.write('Ver JUSTIFICACION_GRUPOS_PREDEFINIDOS.md para más detalles.\n')

        for nombre_grupo in grupos:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Grupo "{nombre_grupo}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'[INFO] Grupo "{nombre_grupo}" ya existe')
                )

        self.stdout.write(
            self.style.SUCCESS('\nInicialización de grupos completada!')
        )
