"""Lógica de depuración de documentación de exenciones.

Compartida por el comando `depurar_exenciones` y la acción del admin.
Borra ARCHIVOS (documentos subidos y constancia PDF) para liberar espacio;
la FILA de la exención nunca se toca: es el histórico que alimenta las
estadísticas y el padrón. La constancia se regenera desde la fila con
`Exencion.regenerar_pdf()`.

Alcance de la depuración de fin de año:
- exenciones RECHAZADAS, o
- exenciones APROBADAS ya vencidas (fecha_vencimiento < hoy).

Quedan protegidas: las vigentes (aprobadas sin vencer) y las en trámite
(borrador, enviada, observada). Las ya depuradas se saltean.
"""
from django.db.models import Q
from django.utils import timezone

from .models import Exencion, ExencionDocumento


def _tamano(field_file):
    try:
        return field_file.size
    except Exception:
        return 0  # el archivo ya no existe en disco


def mb(bytes_):
    return f"{bytes_ / (1024 * 1024):.1f} MB"


def exenciones_depurables(hoy=None):
    hoy = hoy or timezone.localdate()
    return Exencion.objects.filter(documentacion_depurada__isnull=True).filter(
        Q(estado="RECHAZADA") | Q(estado="APROBADA", fecha_vencimiento__lt=hoy)
    )


def resumen(qs, incluir_constancia=True):
    """Qué borraría la depuración, sin borrar nada."""
    docs = ExencionDocumento.objects.filter(exencion__in=qs)
    total_bytes = sum(_tamano(d.archivo) for d in docs)
    constancias = 0
    if incluir_constancia:
        for ex in qs.exclude(certificado_pdf="").exclude(certificado_pdf__isnull=True):
            total_bytes += _tamano(ex.certificado_pdf)
            constancias += 1
    return {
        "exenciones": qs.count(),
        "documentos": docs.count(),
        "constancias": constancias,
        "total_bytes": total_bytes,
    }


def ejecutar(qs, incluir_constancia=True):
    """Borra documentos (y constancia, si corresponde) de cada exención,
    y la marca como depurada. Devuelve el resumen de lo borrado."""
    info = resumen(qs, incluir_constancia)
    ahora = timezone.now()

    for ex in qs:
        # Documentos subidos: la señal post_delete borra el archivo físico.
        ex.documentos.all().delete()
        campos = ["documentacion_depurada"]
        if incluir_constancia and ex.certificado_pdf:
            ex.certificado_pdf.delete(save=False)  # borra el archivo y limpia el campo
            campos.append("certificado_pdf")
        ex.documentacion_depurada = ahora
        ex.save(update_fields=campos)

    info["marcadas"] = info["exenciones"]
    return info
