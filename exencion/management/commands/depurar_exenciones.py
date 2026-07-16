"""Depuración de documentación de exenciones — pasada de fin de año.

Como todas las exenciones vencen el 1 de enero, este comando se corre a
mano una vez al año para liberar el disco de todo lo vencido o rechazado.

Borra los archivos (documentos subidos y constancia PDF); la fila de la
exención se conserva —es el histórico— y la constancia se regenera con
`Exencion.regenerar_pdf()`.

Por defecto SIMULA: muestra qué borraría. Solo borra con --ejecutar.
No está pensado para cron: se ejecuta cuando la DAV lo decide.

Ejemplos:
  manage.py depurar_exenciones                     (simula)
  manage.py depurar_exenciones --ejecutar          (borra documentos + constancia)
  manage.py depurar_exenciones --solo-documentos --ejecutar   (conserva las constancias)
"""
from django.core.management.base import BaseCommand

from exencion import depuracion


class Command(BaseCommand):
    help = (
        "Depura documentación de exenciones vencidas o rechazadas, conservando los datos. "
        "Simula por defecto; borra solo con --ejecutar."
    )

    def add_arguments(self, parser):
        parser.add_argument("--ejecutar", action="store_true",
                            help="Borra en serio. Sin este flag solo simula.")
        parser.add_argument("--solo-documentos", action="store_true", dest="solo_documentos",
                            help="Conserva las constancias PDF; borra solo los documentos subidos.")

    def handle(self, *args, **opts):
        incluir_constancia = not opts["solo_documentos"]
        qs = depuracion.exenciones_depurables()
        info = depuracion.resumen(qs, incluir_constancia=incluir_constancia)

        modo = "EJECUTANDO" if opts["ejecutar"] else "SIMULACIÓN (nada se borra sin --ejecutar)"
        self.stdout.write(self.style.WARNING(f"── Depuración de exenciones · {modo} ──"))
        alcance = "documentos + constancia" if incluir_constancia else "solo documentos"
        self.stdout.write(f"Alcance: vencidas o rechazadas · {alcance}")
        self.stdout.write(
            f"Exenciones: {info['exenciones']} · Documentos: {info['documentos']} · "
            f"Constancias: {info['constancias']} · Espacio a liberar: {depuracion.mb(info['total_bytes'])}"
        )

        if info["exenciones"] == 0:
            self.stdout.write("Nada para depurar.")
            return

        if not opts["ejecutar"]:
            self.stdout.write(self.style.SUCCESS(
                "Simulación terminada. Repetir con --ejecutar para borrar."
            ))
            return

        resultado = depuracion.ejecutar(qs, incluir_constancia=incluir_constancia)
        self.stdout.write(self.style.SUCCESS(
            f"Listo: {resultado['documentos']} documentos y {resultado['constancias']} constancia(s) "
            f"borradas ({depuracion.mb(resultado['total_bytes'])} liberados). "
            f"{resultado['marcadas']} exenciones archivadas."
        ))
