"""Lógica de depuración de documentación presentada.

Compartida por el comando `depurar_documentacion` y la acción del admin.
Borra ARCHIVOS (documentos de postulación e integrantes); los DATOS de
las postulaciones nunca se tocan, así las estadísticas históricas quedan
intactas.
"""
from django.utils import timezone

from .models import Postulacion, DocumentoPostulacion, DocumentoIntegrante

ESTADOS_GANADOR = {"seleccionado", "finalizado"}

TIPOS_VALIDOS = (
    {v for v, _ in DocumentoPostulacion.TIPOS}
    | {v for v, _ in DocumentoIntegrante.TIPOS}
)


def _tamano(field_file):
    try:
        return field_file.size
    except Exception:
        return 0  # el archivo ya no existe en disco


def postulaciones_depurables(convocatorias=None, incluir_ganadores=False,
                             postulacion_id=None):
    """Postulaciones alcanzables por la depuración: siempre de
    convocatorias cerradas; ganadoras solo si se pide explícitamente."""
    hoy = timezone.localdate()
    qs = Postulacion.objects.filter(convocatoria__fecha_fin__lt=hoy)
    if postulacion_id:
        qs = qs.filter(pk=postulacion_id)
    elif convocatorias is not None:
        qs = qs.filter(convocatoria__in=convocatorias)
    if not incluir_ganadores:
        qs = qs.exclude(estado__in=ESTADOS_GANADOR)
    return qs


def ganadoras_protegidas(convocatorias=None, postulacion_id=None):
    """Ganadoras dentro del alcance que quedarían protegidas."""
    hoy = timezone.localdate()
    qs = Postulacion.objects.filter(
        convocatoria__fecha_fin__lt=hoy, estado__in=ESTADOS_GANADOR
    )
    if postulacion_id:
        qs = qs.filter(pk=postulacion_id)
    elif convocatorias is not None:
        qs = qs.filter(convocatoria__in=convocatorias)
    return qs


def documentos_de(postulaciones, tipos=None):
    docs_post = DocumentoPostulacion.objects.filter(postulacion__in=postulaciones)
    docs_int = DocumentoIntegrante.objects.filter(integrante__postulacion__in=postulaciones)
    if tipos:
        docs_post = docs_post.filter(tipo__in=tipos)
        docs_int = docs_int.filter(tipo__in=tipos)
    return docs_post, docs_int


def resumen(postulaciones, tipos=None):
    """Qué borraría la depuración, sin borrar nada."""
    docs_post, docs_int = documentos_de(postulaciones, tipos)

    por_conv = {}
    for d in docs_post.select_related("postulacion__convocatoria"):
        titulo = d.postulacion.convocatoria.titulo
        por_conv[titulo] = por_conv.get(titulo, 0) + 1
    for d in docs_int.select_related("integrante__postulacion__convocatoria"):
        titulo = d.integrante.postulacion.convocatoria.titulo
        por_conv[titulo] = por_conv.get(titulo, 0) + 1

    return {
        "postulaciones": postulaciones.count(),
        "total_docs": docs_post.count() + docs_int.count(),
        "total_bytes": sum(_tamano(d.archivo) for d in docs_post)
                     + sum(_tamano(d.archivo) for d in docs_int),
        "por_conv": sorted(por_conv.items(), key=lambda x: -x[1]),
    }


def ejecutar(postulaciones, tipos=None):
    """Borra los documentos (las señales post_delete eliminan los archivos
    físicos) y marca las postulaciones que quedaron sin documentación."""
    docs_post, docs_int = documentos_de(postulaciones, tipos)

    total_docs = docs_post.count() + docs_int.count()
    total_bytes = sum(_tamano(d.archivo) for d in docs_post) \
                + sum(_tamano(d.archivo) for d in docs_int)

    ids_afectadas = set(docs_post.values_list("postulacion_id", flat=True)) \
                  | set(docs_int.values_list("integrante__postulacion_id", flat=True))
    docs_post.delete()
    docs_int.delete()

    sin_docs = (
        Postulacion.objects.filter(pk__in=ids_afectadas)
        .exclude(documentos__isnull=False)
        .exclude(integrantes__documentos__isnull=False)
    )
    marcadas = sin_docs.update(documentacion_depurada=timezone.now())

    return {"total_docs": total_docs, "total_bytes": total_bytes, "marcadas": marcadas}


def mb(bytes_):
    return f"{bytes_ / (1024 * 1024):.1f} MB"
