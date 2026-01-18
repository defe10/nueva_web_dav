from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from registro_audiovisual.models import PersonaHumana, PersonaJuridica


def _admin_change_url_for(obj):
    """
    Devuelve la URL del change form del admin para un objeto (PersonaHumana o PersonaJuridica).
    """
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=[obj.pk]
    )


def _get_fecha(obj):
    """
    Intenta obtener una fecha de registro/renovación con nombres comunes.
    Ajustá acá si vos tenés un campo definitivo (ej: fecha_registro).
    """
    return (
        getattr(obj, "fecha_renovacion", None)
        or getattr(obj, "fecha_registro", None)
        or getattr(obj, "fecha_creacion", None)
        or getattr(obj, "created_at", None)
    )


@staff_member_required
def nomina_registro(request):
    q = (request.GET.get("q") or "").strip()

    humanas_qs = PersonaHumana.objects.select_related("user").all()
    juridicas_qs = PersonaJuridica.objects.select_related("user").all()

    if q:
        humanas_qs = humanas_qs.filter(
            Q(nombre_completo__icontains=q) |
            Q(user__email__icontains=q)
        )
        juridicas_qs = juridicas_qs.filter(
            Q(razon_social__icontains=q) |
            Q(user__email__icontains=q)
        )

    rows = []

    # Persona Humana
    for ph in humanas_qs:
        display = (getattr(ph, "nombre_completo", "") or "").strip()
        email = getattr(getattr(ph, "user", None), "email", "") or ""
        fecha = _get_fecha(ph)

        rows.append({
            "id": ph.id,
            "display": display or "(sin nombre)",
            "tipo": "Persona humana",
            "email": email,
            "fecha": fecha,
            "url_admin": _admin_change_url_for(ph),
        })

    # Persona Jurídica
    for pj in juridicas_qs:
        display = (getattr(pj, "razon_social", "") or "").strip()
        email = getattr(getattr(pj, "user", None), "email", "") or ""
        fecha = _get_fecha(pj)

        rows.append({
            "id": pj.id,
            "display": display or "(sin razón social)",
            "tipo": "Persona jurídica",
            "email": email,
            "fecha": fecha,
            "url_admin": _admin_change_url_for(pj),
        })

    # Orden por fecha (más reciente primero). Los None al final.
    rows.sort(key=lambda r: (r["fecha"] is None, r["fecha"]), reverse=True)

    return render(request, "backoffice/nomina_registro.html", {
        "q": q,
        "rows": rows,
    })


@staff_member_required
def nomina_registro_excel(request):
    q = (request.GET.get("q") or "").strip()

    humanas_qs = PersonaHumana.objects.select_related("user").all()
    juridicas_qs = PersonaJuridica.objects.select_related("user").all()

    if q:
        humanas_qs = humanas_qs.filter(
            Q(nombre_completo__icontains=q) |
            Q(user__email__icontains=q)
        )
        juridicas_qs = juridicas_qs.filter(
            Q(razon_social__icontains=q) |
            Q(user__email__icontains=q)
        )

    wb = Workbook()
    # quitamos la hoja por defecto
    wb.remove(wb.active)

    def fmt_value(v):
        if v is None:
            return ""
        # datetimes / dates
        try:
            return timezone.localtime(v).strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        try:
            return v.strftime("%d/%m/%Y")
        except Exception:
            pass
        # archivos
        try:
            # FileField puede ser FieldFile
            if hasattr(v, "url") or hasattr(v, "name"):
                return getattr(v, "name", "") or ""
        except Exception:
            pass
        return str(v)

    def model_field_names(model_cls):
        """
        Exporta TODOS los campos concretos del modelo (columnas reales de la DB).
        Excluye relaciones (FK se exporta como su id automáticamente por Django con attname).
        """
        names = []
        for f in model_cls._meta.fields:
            # _meta.fields ya son campos concretos; para FK, usamos attname (ej: user_id)
            names.append(getattr(f, "attname", f.name))
        return names

    def write_sheet(title, qs, model_cls, extra_cols_fn=None):
        ws = wb.create_sheet(title=title)

        field_names = model_field_names(model_cls)

        # Extras (por ejemplo user_email)
        extra_headers = []
        if extra_cols_fn:
            extra_headers = list(extra_cols_fn()["headers"])

        headers = field_names + extra_headers
        ws.append(headers)

        # filas
        for obj in qs:
            row = []
            for name in field_names:
                row.append(fmt_value(getattr(obj, name, "")))

            if extra_cols_fn:
                extras = extra_cols_fn(obj)["values"]
                row.extend([fmt_value(x) for x in extras])

            ws.append(row)

        # anchos razonables (sin volverte loco)
        for col_idx, h in enumerate(headers, start=1):
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max(len(str(h)) + 2, 14), 45)

    def extra_user_email(obj=None):
        if obj is None:
            return {"headers": ["user_email"]}
        u = getattr(obj, "user", None)
        return {"headers": ["user_email"], "values": [getattr(u, "email", "") if u else ""]}

    write_sheet("Personas Humanas", humanas_qs, PersonaHumana, extra_cols_fn=extra_user_email)
    write_sheet("Personas Jurídicas", juridicas_qs, PersonaJuridica, extra_cols_fn=extra_user_email)

    filename = "padron_registro_completo.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
