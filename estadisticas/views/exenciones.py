"""Dashboard y exportación de exenciones impositivas.

Unidades: todas las tablas cuentan SOLICITUDES de exención (sin
borradores). El filtro de año usa la fecha de creación de la solicitud.

Filtros: año, estado y localidad fiscal.
"""
from datetime import date

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

import openpyxl

from exencion.models import Exencion, ESTADOS_EXENCION
from registro_audiovisual.models import LUGARES_RESIDENCIA

from .comun import conteo, filas_barras, write_headers, tabla_resumen, autowidth


ESTADO_EXENCION_MAP = dict(ESTADOS_EXENCION)
LUGAR_MAP           = dict(LUGARES_RESIDENCIA)


def _filtros(request):
    return {
        "anio":   request.GET.get("anio", ""),
        "estado": request.GET.get("estado", ""),
        "loc":    request.GET.get("loc", ""),
    }


def _queryset(filtros):
    qs = Exencion.objects.exclude(estado="BORRADOR")
    if filtros["anio"]:
        qs = qs.filter(fecha_creacion__year=filtros["anio"])
    if filtros["estado"]:
        qs = qs.filter(estado=filtros["estado"])
    if filtros["loc"]:
        qs = qs.filter(localidad_fiscal=filtros["loc"])
    return qs


def _tipo_solicitante(qs):
    return [
        {"label": "Persona humana",
         "total": qs.filter(persona_humana__isnull=False).count()},
        {"label": "Persona jurídica",
         "total": qs.filter(persona_juridica__isnull=False).count()},
        {"label": "Sin vínculo al registro",
         "total": qs.filter(persona_humana__isnull=True, persona_juridica__isnull=True).count()},
    ]


@staff_member_required
def dashboard_exencion(request):
    filtros = _filtros(request)
    qs = _queryset(filtros)

    base = Exencion.objects.exclude(estado="BORRADOR")
    anios = (
        base.values_list("fecha_creacion__year", flat=True)
        .distinct()
        .order_by("-fecha_creacion__year")
    )

    # Evolución anual: compara años, ignora el filtro de año
    base_evolucion = _queryset({**filtros, "anio": ""})
    evolucion = filas_barras(sorted(
        (r["label"], r["total"])
        for r in conteo(base_evolucion, "fecha_creacion__year", {})
    ))

    return render(request, "estadisticas/dashboard_exencion.html", {
        "filtros":   filtros,
        "anios":     anios,
        "estados":   ESTADOS_EXENCION,
        "lugares":   LUGARES_RESIDENCIA,
        "total":     qs.count(),
        "aprobadas": qs.filter(estado="APROBADA").count(),
        "vigentes":  qs.filter(estado="APROBADA", fecha_vencimiento__gte=date.today()).count(),
        "evolucion_solicitudes": evolucion,
        "por_estado":       conteo(qs, "estado", ESTADO_EXENCION_MAP),
        "por_localidad":    conteo(qs, "localidad_fiscal", LUGAR_MAP),
        "tipo_solicitante": _tipo_solicitante(qs),
    })


@staff_member_required
def exportar_exenciones(request):
    filtros = _filtros(request)
    qs = _queryset(filtros).select_related("user")

    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "Solicitudes"
    write_headers(ws1, [
        "Constancia", "Nombre / Razón social", "CUIT", "Estado",
        "Localidad fiscal", "Tipo de solicitante",
        "Fecha solicitud", "Fecha emisión", "Fecha vencimiento",
    ])
    for e in qs.order_by("-fecha_creacion"):
        if e.persona_humana_id:
            tipo = "Persona humana"
        elif e.persona_juridica_id:
            tipo = "Persona jurídica"
        else:
            tipo = "Sin vínculo al registro"
        ws1.append([
            e.numero_constancia,
            e.nombre_razon_social,
            e.cuit,
            e.get_estado_display(),
            e.localidad_fiscal_label or "Sin dato",
            tipo,
            e.fecha_creacion.strftime("%d/%m/%Y"),
            e.fecha_emision.strftime("%d/%m/%Y") if e.fecha_emision else "",
            e.fecha_vencimiento.strftime("%d/%m/%Y") if e.fecha_vencimiento else "",
        ])
    autowidth(ws1)

    ws2 = wb.create_sheet("Resumen")
    fila = 1
    fila = tabla_resumen(ws2, fila, "Por estado",
                         [(r["label"], r["total"]) for r in conteo(qs, "estado", ESTADO_EXENCION_MAP)])
    fila = tabla_resumen(ws2, fila, "Tipo de solicitante",
                         [(r["label"], r["total"]) for r in _tipo_solicitante(qs)])
    fila = tabla_resumen(ws2, fila, "Por año de solicitud",
                         [(r["label"], r["total"]) for r in conteo(qs, "fecha_creacion__year", {})])
    fila = tabla_resumen(ws2, fila, "Localidad fiscal",
                         [(r["label"], r["total"]) for r in conteo(qs, "localidad_fiscal", LUGAR_MAP)])
    autowidth(ws2)

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="estadisticas_exenciones.xlsx"'
    wb.save(resp)
    return resp
