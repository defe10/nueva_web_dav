"""Utilidades para vincular campos de la Obra (dirección, producción) con
el Registro Audiovisual (PersonaHumana / PersonaJuridica).

La idea: un campo de texto libre que, si coincide con alguien del registro,
queda además vinculado mediante un GenericForeignKey. Estas funciones
centralizan la búsqueda y el "cómo se muestra" cada tipo de registro para que
el endpoint AJAX, el formulario, el admin y los templates hablen el mismo idioma.
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

# Modelos del registro que se pueden vincular. El orden define la prioridad
# de aparición en el buscador.
MODELOS_VINCULABLES = (PersonaHumana, PersonaJuridica)


def label_for(obj):
    """Texto legible de un registro (para el input y para mostrar el vínculo)."""
    if isinstance(obj, PersonaHumana):
        return f"{obj.nombre} {obj.apellido}".strip()
    if isinstance(obj, PersonaJuridica):
        return obj.nombre_comercial or obj.razon_social
    return str(obj)


def _sublabel_for(obj):
    """Dato secundario (CUIL/CUIT, tipo) para desambiguar en el buscador."""
    if isinstance(obj, PersonaHumana):
        return f"CUIL {obj.cuil_cuit}"
    if isinstance(obj, PersonaJuridica):
        return f"CUIT {obj.cuil_cuit}"
    return ""


def _tipo_display(obj):
    return "Persona" if isinstance(obj, PersonaHumana) else "Entidad jurídica"


def _ct_id(modelo):
    return ContentType.objects.get_for_model(modelo).id


def buscar(termino, limite=20):
    """Busca en ambos registros y devuelve resultados normalizados.

    Cada item: {ct, id, label, sublabel, tipo} donde `ct` es el id del
    ContentType e `id` el pk del objeto: juntos identifican el vínculo.
    """
    termino = (termino or "").strip()
    if not termino:
        return []

    resultados = []

    humanas = PersonaHumana.objects.filter(
        Q(nombre__icontains=termino)
        | Q(apellido__icontains=termino)
        | Q(cuil_cuit__icontains=termino)
    )[:limite]
    ct_humana = _ct_id(PersonaHumana)
    for p in humanas:
        resultados.append({
            "ct": ct_humana, "id": p.pk,
            "label": label_for(p), "sublabel": _sublabel_for(p),
            "tipo": _tipo_display(p),
        })

    juridicas = PersonaJuridica.objects.filter(
        Q(razon_social__icontains=termino)
        | Q(nombre_comercial__icontains=termino)
        | Q(cuil_cuit__icontains=termino)
    )[:limite]
    ct_juridica = _ct_id(PersonaJuridica)
    for j in juridicas:
        resultados.append({
            "ct": ct_juridica, "id": j.pk,
            "label": label_for(j), "sublabel": _sublabel_for(j),
            "tipo": _tipo_display(j),
        })

    return resultados[:limite]
