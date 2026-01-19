from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Crea los grupos base del sistema (si no existen)."

    def handle(self, *args, **options):
        grupos = ["jurado", "admin", "usuario"]

        for g in grupos:
            Group.objects.get_or_create(name=g)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: grupos asegurados: {', '.join(grupos)}"
            )
        )
