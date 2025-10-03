from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        grupos = [
            'Admin Sistema',
            'Admin Empresa',
            'Validador Financiero',
            'Validador Abastecimiento',
            'Solicitante',
        ]

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
            self.style.SUCCESS('\nInicializacion de grupos completada!')
        )
