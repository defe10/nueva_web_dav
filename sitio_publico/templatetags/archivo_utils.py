from django import template
import os

register = template.Library()

@register.filter
def nombre_original(value):
    """
    Limpia el nombre de archivo generado por Django,
    independientemente del upload_to.

    Ej:
    'postulaciones/documentos/cuadro_honorarios_j9ICGzH.pdf' -> 'cuadro_honorarios.pdf'
    'exencion/documentos/constancia_dgr_X8aPq2.pdf' -> 'constancia_dgr.pdf'
    """
    if not value:
        return ""

    nombre = os.path.basename(str(value))
    base, ext = os.path.splitext(nombre)

    if "_" in base:
        base = base.rsplit("_", 1)[0]

    return f"{base}{ext}"
