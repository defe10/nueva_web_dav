from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Crea grupos base del sistema (si no existen)."

    def handle(self, *args, **options):
        grupos = ["jurado"]
        for g in grupos:
            Group.objects.get_or_create(name=g)
        self.stdout.write(self.style.SUCCESS(f"OK: grupos asegurados: {', '.join(grupos)}"))
