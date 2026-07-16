"""Impacto económico: rendiciones aprobadas del Plan de Fomento.

Unidades:
- Montos en pesos (Decimal, agregados en la base de datos).
- Cantidades = contrataciones / ítems declarados por categoría; una misma
  persona puede aparecer en más de una categoría o rendición, por lo que
  NO representan personas únicas.

La referencia temporal es la fecha de aprobación de la rendición
(Rendicion.fecha_aprobacion), no el año de envío de la postulación.
"""
from decimal import Decimal

from django.db.models import Count, Sum

from convocatorias.models import Postulacion, Rendicion

from .comun import ESTADOS_GANADOR, pct


CAMPOS_IMPACTO = [
    ("honorarios_tecnicos",     "Honorarios técnicos"),
    ("honorarios_elenco",       "Honorarios elenco"),
    ("otros_honorarios",        "Otros honorarios"),
    ("insumos",                 "Insumos"),
    ("servicios_audiovisuales", "Servicios audiovisuales"),
    ("servicios_logistica",     "Servicios / logística"),
]


def impacto(filtros):
    qs = Rendicion.objects.filter(estado="APROBADO")
    if filtros.get("conv"):
        qs = qs.filter(postulacion__convocatoria_id=filtros["conv"])
    if filtros.get("anio"):
        qs = qs.filter(fecha_aprobacion__year=filtros["anio"])

    agregados = qs.aggregate(
        cantidad_rendiciones=Count("id"),
        **{campo: Sum(campo) for campo, _ in CAMPOS_IMPACTO},
        **{f"{campo}_cantidad": Sum(f"{campo}_cantidad") for campo, _ in CAMPOS_IMPACTO},
    )

    cero = Decimal("0")
    totales    = {campo: agregados[campo] or cero for campo, _ in CAMPOS_IMPACTO}
    cantidades = {campo: agregados[f"{campo}_cantidad"] or 0 for campo, _ in CAMPOS_IMPACTO}

    total_general = sum(totales.values(), cero)
    return {
        "impacto_filas": [
            {"label": label, "monto": totales[campo], "cantidad": cantidades[campo],
             "pct": round(totales[campo] / total_general * 100, 1) if total_general else 0}
            for campo, label in CAMPOS_IMPACTO
        ],
        "impacto_total": total_general,
        "impacto_total_cantidad": sum(cantidades.values()),
        "impacto_count": agregados["cantidad_rendiciones"],
        **montos_comparados(filtros),
    }


# Estados de rendición cuyos montos cuentan como "rendido":
# fue presentada y no fue rechazada (el borrador aún no declara nada).
ESTADOS_RENDIDO = ("ENVIADO", "OBSERVADO", "SUBSANADO", "APROBADO")


def _suma_categorias(qs):
    agg = qs.aggregate(**{campo: Sum(campo) for campo, _ in CAMPOS_IMPACTO})
    return sum((agg[campo] or Decimal("0") for campo, _ in CAMPOS_IMPACTO), Decimal("0"))


def montos_comparados(filtros):
    """Monto otorgado (postulaciones ganadoras), rendido (rendiciones
    presentadas) y aprobado (rendiciones aprobadas), con % de ejecución.

    Con filtro de año: otorgado usa el año de envío de la postulación,
    rendido el año de envío de la rendición y aprobado el año de aprobación.
    """
    ganadoras = Postulacion.objects.filter(estado__in=ESTADOS_GANADOR)
    rendidas  = Rendicion.objects.filter(estado__in=ESTADOS_RENDIDO)
    aprobadas = Rendicion.objects.filter(estado="APROBADO")

    if filtros.get("conv"):
        ganadoras = ganadoras.filter(convocatoria_id=filtros["conv"])
        rendidas  = rendidas.filter(postulacion__convocatoria_id=filtros["conv"])
        aprobadas = aprobadas.filter(postulacion__convocatoria_id=filtros["conv"])
    if filtros.get("anio"):
        ganadoras = ganadoras.filter(fecha_envio__year=filtros["anio"])
        rendidas  = rendidas.filter(fecha_envio__year=filtros["anio"])
        aprobadas = aprobadas.filter(fecha_aprobacion__year=filtros["anio"])

    otorgado = ganadoras.aggregate(t=Sum("monto_otorgado"))["t"] or Decimal("0")
    rendido  = _suma_categorias(rendidas)
    aprobado = _suma_categorias(aprobadas)

    return {
        "monto_otorgado": otorgado,
        "monto_rendido":  rendido,
        "monto_aprobado": aprobado,
        "pct_ejecucion":  pct(aprobado, otorgado),
        "ganadoras_sin_monto": ganadoras.filter(monto_otorgado__isnull=True).count(),
    }
