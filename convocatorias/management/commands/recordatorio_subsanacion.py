"""
Envía recordatorios por email a postulantes con subsanaciones pendientes.

Uso manual:
    python manage.py recordatorio_subsanacion
    python manage.py recordatorio_subsanacion --dias 5    # solo si la obs tiene >= 5 días sin subsanar (default)

Configurar en cron (ej. cada día a las 9):
    0 9 * * * /ruta/al/venv/bin/python /ruta/al/proyecto/manage.py recordatorio_subsanacion --dias 5
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from convocatorias.models import ObservacionAdministrativa


class Command(BaseCommand):
    help = "Envía recordatorios a postulantes con subsanaciones pendientes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=5,
            help="Solo enviar si la observación tiene al menos X días sin subsanar. Default: 5.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra a quiénes se enviaría sin enviar realmente.",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        dry_run = options["dry_run"]

        qs = (
            ObservacionAdministrativa.objects
            .filter(subsanada=False)
            .select_related("postulacion__user", "postulacion__convocatoria")
            .order_by("postulacion__user", "postulacion")
        )

        if dias > 0:
            desde = timezone.now() - timezone.timedelta(days=dias)
            qs = qs.filter(fecha_creacion__lte=desde)

        # Agrupar por postulacion para enviar un solo email por postulación
        por_postulacion = {}
        for obs in qs:
            pid = obs.postulacion_id
            if pid not in por_postulacion:
                por_postulacion[pid] = {"postulacion": obs.postulacion, "observaciones": []}
            por_postulacion[pid]["observaciones"].append(obs)

        if not por_postulacion:
            self.stdout.write("No hay subsanaciones pendientes que notificar.")
            return

        enviados = 0
        errores = 0

        for pid, datos in por_postulacion.items():
            postulacion = datos["postulacion"]
            observaciones = datos["observaciones"]
            user = postulacion.user

            if not user.email:
                self.stdout.write(self.style.WARNING(
                    f"  Omitido (sin email): postulación {pid} — {user.username}"
                ))
                continue

            convocatoria_titulo = postulacion.convocatoria.titulo if postulacion.convocatoria else ""
            panel_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/usuarios/panel/"

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Enviaría recordatorio a {user.email} "
                    f"({len(observaciones)} obs pendiente/s — postulación {pid})"
                )
                continue

            contexto = {
                "user": user,
                "postulacion": postulacion,
                "convocatoria_titulo": convocatoria_titulo,
                "observaciones": observaciones,
                "panel_url": panel_url,
                "anio": timezone.now().year,
            }

            asunto = f"Recordatorio: tenés documentación pendiente de subsanar — {convocatoria_titulo}"
            texto = (
                f"Hola {user.get_full_name() or user.username},\n\n"
                f"Te recordamos que tenés documentación pendiente de subsanar en la convocatoria "
                f'"{convocatoria_titulo}".\n\n'
                f"Ingresá al panel para regularizar tu situación: {panel_url}\n"
            )

            try:
                try:
                    html = render_to_string("convocatorias/subsanacion_documentacion_email.html", contexto)
                except Exception:
                    html = None

                email = EmailMultiAlternatives(
                    subject=asunto,
                    body=texto,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    to=[user.email],
                )
                if html:
                    email.attach_alternative(html, "text/html")
                email.send(fail_silently=False)

                self.stdout.write(self.style.SUCCESS(
                    f"  Enviado a {user.email} — postulación {pid} "
                    f"({len(observaciones)} obs pendiente/s)"
                ))
                enviados += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"  Error enviando a {user.email}: {e}"
                ))
                errores += 1

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"\nListo. Enviados: {enviados}. Errores: {errores}.")
            )
