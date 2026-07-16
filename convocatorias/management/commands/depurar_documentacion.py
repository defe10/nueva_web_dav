"""Depuración manual de documentación presentada.

Borra los ARCHIVOS presentados (documentos de postulación y de
integrantes) para liberar espacio. Los DATOS de las postulaciones
(estados, montos, rendiciones, personas) nunca se tocan: las
estadísticas históricas quedan intactas.

Por defecto es una SIMULACIÓN: muestra qué borraría y cuánto espacio
libera. Solo borra con --ejecutar. No está pensado para cron ni tareas
programadas: se corre a mano cuando la DAV lo decide.

Protecciones:
- Solo alcanza postulaciones de convocatorias ya cerradas.
- Las ganadoras (seleccionado / finalizado) quedan afuera salvo que se
  pase --incluir-ganadores explícitamente.
- Cada postulación que queda sin documentos se marca con la fecha de
  depuración, visible en el admin.

La lógica compartida con la acción del admin vive en
convocatorias/depuracion.py.

Ejemplos:
  manage.py depurar_documentacion                      (simula: no ganadoras)
  manage.py depurar_documentacion --ejecutar           (borra eso mismo)
  manage.py depurar_documentacion --conv 5 --ejecutar
  manage.py depurar_documentacion --incluir-ganadores --tipos DNI,CV_BIOFILMOGRAFIA
  manage.py depurar_documentacion --huerfanos          (archivos sin registro en la base)
"""
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from convocatorias import depuracion
from convocatorias.models import Convocatoria


class Command(BaseCommand):
    help = (
        "Borra documentación presentada para liberar espacio, conservando todos los datos. "
        "Simula por defecto; borra solo con --ejecutar."
    )

    def add_arguments(self, parser):
        parser.add_argument("--ejecutar", action="store_true",
                            help="Borra en serio. Sin este flag solo simula.")
        parser.add_argument("--conv", type=int,
                            help="Limitar a una convocatoria (id).")
        parser.add_argument("--postulacion", type=int,
                            help="Limitar a una postulación puntual (id).")
        parser.add_argument("--incluir-ganadores", action="store_true", dest="incluir_ganadores",
                            help="Incluye también seleccionadas y finalizadas.")
        parser.add_argument("--tipos", type=str,
                            help="Borrado parcial: solo estos tipos de documento (separados por coma).")
        parser.add_argument("--huerfanos", action="store_true",
                            help="Modo aparte: borra archivos de media/ que ninguna fila de la base referencia.")

    def handle(self, *args, **opts):
        if opts["huerfanos"]:
            self._huerfanos(opts["ejecutar"])
            return

        tipos = None
        if opts["tipos"]:
            tipos = [t.strip().upper() for t in opts["tipos"].split(",") if t.strip()]
            invalidos = [t for t in tipos if t not in depuracion.TIPOS_VALIDOS]
            if invalidos:
                raise CommandError(
                    f"Tipos inválidos: {', '.join(invalidos)}. "
                    f"Válidos: {', '.join(sorted(depuracion.TIPOS_VALIDOS))}"
                )

        convocatorias = None
        if opts["conv"]:
            convocatorias = Convocatoria.objects.filter(pk=opts["conv"])

        qs = depuracion.postulaciones_depurables(
            convocatorias=convocatorias,
            incluir_ganadores=opts["incluir_ganadores"],
            postulacion_id=opts["postulacion"],
        )
        protegidas = depuracion.ganadoras_protegidas(
            convocatorias=convocatorias, postulacion_id=opts["postulacion"],
        )

        if opts["postulacion"]:
            if not opts["incluir_ganadores"] and protegidas.exists():
                raise CommandError(
                    "Esa postulación es ganadora (seleccionada/finalizada). "
                    "Para depurarla igual, agregá --incluir-ganadores."
                )
            if not qs.exists() and not protegidas.exists():
                raise CommandError(
                    f"La postulación {opts['postulacion']} no existe o su convocatoria sigue abierta."
                )

        info = depuracion.resumen(qs, tipos)

        # ── Resumen ──────────────────────────────────────────
        modo = "EJECUTANDO" if opts["ejecutar"] else "SIMULACIÓN (nada se borra sin --ejecutar)"
        self.stdout.write(self.style.WARNING(f"── Depuración de documentación · {modo} ──"))
        alcance = "incluye ganadoras" if opts["incluir_ganadores"] else "ganadoras protegidas"
        parcial = f" · solo tipos: {', '.join(tipos)}" if tipos else ""
        self.stdout.write(f"Alcance: convocatorias cerradas · {alcance}{parcial}")
        self.stdout.write(
            f"Postulaciones alcanzadas: {info['postulaciones']} · "
            f"Documentos a borrar: {info['total_docs']} · "
            f"Espacio a liberar: {depuracion.mb(info['total_bytes'])}"
        )
        for titulo, cant in info["por_conv"]:
            self.stdout.write(f"  · {titulo}: {cant} documentos")

        if not opts["incluir_ganadores"] and protegidas.exists():
            self.stdout.write(self.style.NOTICE(
                f"Protegidas: {protegidas.count()} postulaciones ganadoras "
                "(usar --incluir-ganadores para alcanzarlas)."
            ))

        if info["total_docs"] == 0:
            self.stdout.write("Nada para borrar.")
            return

        if not opts["ejecutar"]:
            self.stdout.write(self.style.SUCCESS(
                "Simulación terminada. Repetir con --ejecutar para borrar."
            ))
            return

        # ── Borrado real ─────────────────────────────────────
        resultado = depuracion.ejecutar(qs, tipos)
        self.stdout.write(self.style.SUCCESS(
            f"Listo: {resultado['total_docs']} documentos borrados "
            f"({depuracion.mb(resultado['total_bytes'])} liberados). "
            f"{resultado['marcadas']} postulaciones marcadas como depuradas."
        ))

    # ──────────────────────────────────────────────────────────
    # Archivos huérfanos: existen en media/ pero ninguna fila
    # de la base los referencia (restos de versiones anteriores).
    # ──────────────────────────────────────────────────────────
    def _huerfanos(self, ejecutar):
        referenciados = set()
        for modelo in apps.get_models():
            campos = [f for f in modelo._meta.get_fields()
                      if f.__class__.__name__ in ("FileField", "ImageField")]
            for campo in campos:
                for valor in modelo.objects.exclude(**{campo.name: ""}) \
                                           .values_list(campo.name, flat=True):
                    if valor:
                        referenciados.add(os.path.normpath(valor))

        media_root = settings.MEDIA_ROOT
        huerfanos = []
        total_bytes = 0
        for raiz, _dirs, archivos in os.walk(media_root):
            for nombre in archivos:
                ruta = os.path.join(raiz, nombre)
                relativa = os.path.normpath(os.path.relpath(ruta, media_root))
                if relativa not in referenciados:
                    huerfanos.append(relativa)
                    total_bytes += os.path.getsize(ruta)

        modo = "EJECUTANDO" if ejecutar else "SIMULACIÓN (nada se borra sin --ejecutar)"
        self.stdout.write(self.style.WARNING(f"── Archivos huérfanos · {modo} ──"))
        self.stdout.write(
            f"Archivos sin referencia en la base: {len(huerfanos)} · {depuracion.mb(total_bytes)}"
        )
        for ruta in huerfanos[:20]:
            self.stdout.write(f"  · {ruta}")
        if len(huerfanos) > 20:
            self.stdout.write(f"  … y {len(huerfanos) - 20} más")

        if not huerfanos:
            return
        if not ejecutar:
            self.stdout.write(self.style.SUCCESS(
                "Simulación terminada. Repetir con --huerfanos --ejecutar para borrar."
            ))
            return

        for relativa in huerfanos:
            os.remove(os.path.join(media_root, relativa))
        self.stdout.write(self.style.SUCCESS(
            f"Listo: {len(huerfanos)} archivos huérfanos borrados ({depuracion.mb(total_bytes)} liberados)."
        ))
