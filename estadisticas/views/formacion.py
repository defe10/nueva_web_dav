"""Dashboard y exportación de convocatorias de formación.

Unidades: todas las tablas cuentan INSCRIPCIONES. Una misma persona
inscripta en dos convocatorias cuenta dos veces (al filtrar por
convocatoria, cuenta una).

Filtros: convocatoria, año de inscripción y estado.
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpResponse

import openpyxl

from formacion.models import (
    ConvocatoriaFormacion, InscripcionFormacion,
    ESTADOS as ESTADOS_FORMACION, GENERO as GENERO_FORMACION,
    LOCALIDADES as LOCALIDADES_FORMACION, VINCULO_SECTOR, TIPO_FORMACION,
)

from .comun import (
    RANGOS_ETARIOS, conteo, rango, pct, filas_barras,
    write_headers, tabla_resumen, autowidth,
)


ESTADO_FORM_MAP    = dict(ESTADOS_FORMACION)
GENERO_FORM_MAP    = {v: l for v, l in GENERO_FORMACION if v}
LOCALIDAD_FORM_MAP = {v: l for v, l in LOCALIDADES_FORMACION if v}
VINCULO_MAP        = dict(VINCULO_SECTOR)
TIPO_FORMACION_MAP = dict(TIPO_FORMACION)


def _filtros(request):
    return {
        "conv":   request.GET.get("conv", ""),
        "anio":   request.GET.get("anio", ""),
        "estado": request.GET.get("estado", ""),
    }


def _queryset(filtros):
    qs = InscripcionFormacion.objects.all()
    if filtros["conv"]:
        qs = qs.filter(convocatoria_id=filtros["conv"])
    if filtros["anio"]:
        qs = qs.filter(fecha__year=filtros["anio"])
    if filtros["estado"]:
        qs = qs.filter(estado=filtros["estado"])
    return qs


def _rango_etario(qs):
    rangos = {}
    for edad_valor in qs.values_list("edad", flat=True):
        r = rango(edad_valor)
        rangos[r] = rangos.get(r, 0) + 1
    return [
        {"label": label, "total": rangos[label]}
        for label in [r[0] for r in RANGOS_ETARIOS] + ["Sin dato"]
        if label in rangos
    ]


def _datos_incompletos(qs):
    total = qs.count()
    if not total:
        return []
    campos = [
        ("Sin género",    qs.filter(genero="").count()),
        ("Sin edad",      qs.filter(edad__isnull=True).count()),
        ("Sin localidad", qs.filter(localidad="").count()),
        ("Sin vínculo con el sector", qs.filter(vinculo_sector="").count()),
    ]
    return [
        {"label": label, "total": cant, "pct": pct(cant, total)}
        for label, cant in campos if cant
    ]


@staff_member_required
def dashboard_formacion(request):
    filtros = _filtros(request)
    qs = _queryset(filtros)

    anios = (
        InscripcionFormacion.objects
        .values_list("fecha__year", flat=True)
        .distinct()
        .order_by("-fecha__year")
    )

    # Evolución anual: compara años, ignora el filtro de año
    base_evolucion = _queryset({**filtros, "anio": ""})
    evolucion = filas_barras(sorted(
        (r["label"], r["total"])
        for r in conteo(base_evolucion, "fecha__year", {})
    ))

    return render(request, "estadisticas/dashboard_formacion.html", {
        "filtros":              filtros,
        "convocatorias":        ConvocatoriaFormacion.objects.order_by("-fecha_inicio"),
        "anios":                anios,
        "estados":              ESTADOS_FORMACION,
        "total":                qs.count(),
        "total_convocatorias":  ConvocatoriaFormacion.objects.count(),
        "admitidos":            qs.filter(estado="admitido").count(),
        "evolucion_inscripciones": evolucion,
        "datos_incompletos":    _datos_incompletos(qs),
        "por_conv":      conteo(qs, "convocatoria__titulo", {}),
        "por_tipo":      conteo(qs, "convocatoria__tipo_formacion", TIPO_FORMACION_MAP),
        "por_estado":    conteo(qs, "estado", ESTADO_FORM_MAP),
        "por_genero":    conteo(qs, "genero", GENERO_FORM_MAP),
        "por_localidad": conteo(qs, "localidad", LOCALIDAD_FORM_MAP),
        "por_vinculo":   conteo(qs, "vinculo_sector", VINCULO_MAP),
        "rango_etario":  _rango_etario(qs),
    })


@staff_member_required
def exportar_formacion(request):
    filtros = _filtros(request)
    qs = _queryset(filtros).select_related("convocatoria", "user")

    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "Inscripciones"
    write_headers(ws1, [
        "Convocatoria", "Tipo de formación", "Nombre", "Apellido", "DNI",
        "Email", "Estado", "Género", "Edad", "Localidad",
        "Vínculo con el sector", "Fecha de inscripción",
    ])
    for i in qs.order_by("convocatoria", "-fecha"):
        if i.localidad == "otro":
            loc = i.otra_localidad or "Otro (sin especificar)"
        else:
            loc = i.get_localidad_display() if i.localidad else "Sin dato"
        ws1.append([
            i.convocatoria.titulo,
            i.convocatoria.get_tipo_formacion_display(),
            i.nombre, i.apellido, i.dni,
            i.email or i.user.email,
            i.get_estado_display(),
            i.get_genero_display() if i.genero else "Sin dato",
            i.edad if i.edad is not None else "Sin dato",
            loc,
            i.get_vinculo_sector_display() if i.vinculo_sector else "Sin dato",
            i.fecha.strftime("%d/%m/%Y"),
        ])
    autowidth(ws1)

    ws2 = wb.create_sheet("Resumen")
    fila = 1
    fila = tabla_resumen(ws2, fila, "Por convocatoria",
                         [(r["label"], r["total"]) for r in conteo(qs, "convocatoria__titulo", {})])
    fila = tabla_resumen(ws2, fila, "Por estado",
                         [(r["label"], r["total"]) for r in conteo(qs, "estado", ESTADO_FORM_MAP)])
    fila = tabla_resumen(ws2, fila, "Por género",
                         [(r["label"], r["total"]) for r in conteo(qs, "genero", GENERO_FORM_MAP)])
    fila = tabla_resumen(ws2, fila, "Rango etario",
                         [(r["label"], r["total"]) for r in _rango_etario(qs)])
    fila = tabla_resumen(ws2, fila, "Por localidad",
                         [(r["label"], r["total"]) for r in conteo(qs, "localidad", LOCALIDAD_FORM_MAP)])
    fila = tabla_resumen(ws2, fila, "Vínculo con el sector",
                         [(r["label"], r["total"]) for r in conteo(qs, "vinculo_sector", VINCULO_MAP)])
    autowidth(ws2)

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="estadisticas_formacion.xlsx"'
    wb.save(resp)
    return resp
