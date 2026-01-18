# exencion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from convocatorias.models import Convocatoria
from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from .models import Exencion, ExencionDocumento, ObservacionAdministrativaExencion, PadronPublicoExencion
from .utils import datos_fiscales_completos


# ============================================================
# CONFIG
# ============================================================
MAX_ARCHIVOS_EXENCION = 5  # total por exención (inicial + subsanación)


# ============================================================
# HELPERS
# ============================================================
def _es_pdf(archivo):
    nombre = (archivo.name or "").lower()
    content_type = (getattr(archivo, "content_type", "") or "").lower()
    return nombre.endswith(".pdf") or ("pdf" in content_type)


def _cupos_restantes(exencion):
    total_actual = ExencionDocumento.objects.filter(exencion=exencion).count()
    return MAX_ARCHIVOS_EXENCION - total_actual


# ============================================================
# PASO 1 — INICIAR SOLICITUD
# ============================================================
@login_required(login_url="/usuarios/login/")
def iniciar_solicitud(request, convocatoria_id=None):

    convocatoria = None
    if convocatoria_id is not None:
        convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)

    user = request.user

    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    if not (persona_humana or persona_juridica):
        next_url = request.path
        return redirect(f"/registro/seleccionar-tipo/?next={next_url}")

    persona = persona_humana or persona_juridica

    if not datos_fiscales_completos(persona):
        messages.warning(
            request,
            "Para solicitar la exención impositiva es necesario completar previamente "
            "todos los datos fiscales en el Registro Audiovisual "
            "(Situación IVA, Actividad DGR, Domicilio fiscal, Localidad fiscal y Código Postal). "
            "Si elegiste “Ninguna/Ninguno” en IVA o DGR, se considera incompleto."
        )
        next_url = request.path
        if persona_humana:
            return redirect(f"/registro/persona-humana/?next={next_url}")
        return redirect(f"/registro/persona-juridica/?next={next_url}")

    exencion, _creada = Exencion.objects.get_or_create(
        user=user,
        convocatoria=convocatoria,
        defaults={
            "persona_humana": persona_humana,
            "persona_juridica": persona_juridica,
            "nombre_razon_social": (
                getattr(persona, "nombre_completo", None)
                or getattr(persona, "razon_social", "")
                or ""
            ),
            "email": getattr(persona, "email", "") or user.email or "",
            "cuit": getattr(persona, "cuil_cuit", "") or "",
            "domicilio_fiscal": getattr(persona, "domicilio_fiscal", "") or "",
            "localidad_fiscal": getattr(persona, "localidad_fiscal", "") or "",
            "codigo_postal_fiscal": getattr(persona, "codigo_postal_fiscal", "") or "",
            "actividad_dgr": getattr(persona, "actividad_dgr", "") or "",
        }
    )

    return redirect("exencion:documentacion", exencion_id=exencion.id)


# ============================================================
# DOCUMENTACIÓN INICIAL (pantalla)
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documentacion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    persona = exencion.persona_humana or exencion.persona_juridica

    if not datos_fiscales_completos(persona):
        messages.warning(
            request,
            "Para continuar con la solicitud de exención debés completar previamente "
            "todos los datos fiscales en tu Registro Audiovisual. "
            "Si elegiste “Ninguna/Ninguno” en IVA o DGR, se considera incompleto."
        )
        next_url = request.path
        if exencion.persona_humana:
            return redirect(f"/registro/persona-humana/?next={next_url}")
        return redirect(f"/registro/persona-juridica/?next={next_url}")

    documentos_pendientes = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=False,
        estado="PENDIENTE",
    ).order_by("-fecha_subida")

    documentos_enviados = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=False,
        estado="ENVIADO",
    ).order_by("-fecha_subida")

    restantes = _cupos_restantes(exencion)

    return render(
        request,
        "exencion/documentacion.html",
        {
            "exencion": exencion,
            "convocatoria": exencion.convocatoria,
            "documentos_pendientes": documentos_pendientes,
            "documentos_enviados": documentos_enviados,
            "max_archivos": MAX_ARCHIVOS_EXENCION,
            "restantes": restantes,
        }
    )


# ============================================================
# AGREGAR DOCUMENTACIÓN INICIAL (POST)
# ============================================================
@login_required(login_url="/usuarios/login/")
def agregar_documentacion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    archivos = request.FILES.getlist("archivos")
    if not archivos:
        messages.error(request, "Seleccioná al menos un archivo para subir.")
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    restantes = _cupos_restantes(exencion)

    if restantes <= 0:
        messages.error(request, f"Ya alcanzaste el máximo de {MAX_ARCHIVOS_EXENCION} archivos para esta exención.")
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    if len(archivos) > restantes:
        messages.error(
            request,
            f"Podés subir como máximo {restantes} archivo(s) más. Límite total: {MAX_ARCHIVOS_EXENCION}."
        )
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    guardados = 0

    for archivo in archivos:
        if not _es_pdf(archivo):
            messages.error(request, f"El archivo '{archivo.name}' no es PDF.")
            continue

        doc = ExencionDocumento(
            exencion=exencion,
            archivo=archivo,
            es_subsanacion=False,
            estado="PENDIENTE",
        )
        try:
            doc.full_clean()
            doc.save()
            guardados += 1
        except Exception as e:
            messages.error(request, str(e))

    if guardados > 0:
        messages.success(request, f"Se agregaron {guardados} archivo(s).")
    else:
        messages.error(request, "No se pudo subir ningún archivo. Revisá los errores.")

    return redirect("exencion:documentacion", exencion_id=exencion.id)


# ============================================================
# CONFIRMAR ENVÍO DOCUMENTACIÓN INICIAL
# ============================================================
@login_required(login_url="/usuarios/login/")
def confirmar_documentacion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    qs = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=False,
        estado="PENDIENTE",
    )

    if not qs.exists():
        messages.error(request, "No hay documentación pendiente para enviar.")
        return redirect("exencion:documentacion", exencion_id=exencion.id)

    ahora = timezone.now()
    qs.update(estado="ENVIADO", fecha_envio=ahora)

    exencion.estado = "ENVIADA"
    exencion.save(update_fields=["estado"])

    return redirect("exencion:completada", exencion_id=exencion.id)


# ============================================================
# ELIMINAR DOCUMENTO (inicial o subsanado)
# ============================================================
@login_required(login_url="/usuarios/login/")
def eliminar_documento(request, documento_id):

    doc = get_object_or_404(ExencionDocumento, id=documento_id)

    if doc.exencion.user != request.user:
        return redirect("usuarios:panel_usuario")

    if doc.estado != "PENDIENTE":
        messages.error(request, "No se puede eliminar un documento ya enviado.")
        return redirect("usuarios:panel_usuario")

    exencion_id = doc.exencion_id
    es_sub = doc.es_subsanacion

    doc.delete()
    messages.success(request, "Documento eliminado.")

    if es_sub:
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion_id)
    return redirect("exencion:documentacion", exencion_id=exencion_id)


# ============================================================
# CONFIRMACIÓN FINAL (pantalla)
# ============================================================
@login_required(login_url="/usuarios/login/")
def solicitud_completada(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    return render(
        request,
        "exencion/completada.html",
        {"exencion": exencion, "convocatoria": exencion.convocatoria}
    )


# ============================================================
# SUBSANACIÓN (pantalla)
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documento_subsanado_exencion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)

    if exencion.user != request.user:
        return redirect("usuarios:panel_usuario")

    observaciones_pendientes = list(
        ObservacionAdministrativaExencion.objects
        .filter(exencion=exencion, subsanada=False)
        .order_by("-fecha_creacion")
    )

    documentos_pendientes = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=True,
        estado="PENDIENTE",
    ).order_by("-fecha_subida")

    documentos_enviados = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=True,
        estado="ENVIADO",
    ).order_by("-fecha_subida")

    restantes = _cupos_restantes(exencion)

    return render(
        request,
        "exencion/subir_documento_subsanado_exencion.html",
        {
            "exencion": exencion,
            "observaciones_pendientes": observaciones_pendientes,
            "documentos_pendientes": documentos_pendientes,
            "documentos_enviados": documentos_enviados,
            "max_archivos": MAX_ARCHIVOS_EXENCION,
            "restantes": restantes,
        }
    )


# ============================================================
# AGREGAR DOCUMENTOS SUBSANADOS (POST)
# ============================================================
@login_required(login_url="/usuarios/login/")
def agregar_documento_subsanado_exencion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("usuarios:panel_usuario")

    if request.method != "POST":
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    archivos = request.FILES.getlist("archivos")
    if not archivos:
        messages.error(request, "Seleccioná al menos un archivo para subir.")
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    restantes = _cupos_restantes(exencion)

    if restantes <= 0:
        messages.error(request, f"Ya alcanzaste el máximo de {MAX_ARCHIVOS_EXENCION} archivos para esta exención.")
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    if len(archivos) > restantes:
        messages.error(
            request,
            f"Podés subir como máximo {restantes} archivo(s) más. Límite total: {MAX_ARCHIVOS_EXENCION}."
        )
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    guardados = 0
    for archivo in archivos:
        if not _es_pdf(archivo):
            messages.error(request, f"El archivo '{archivo.name}' no es PDF.")
            continue

        doc = ExencionDocumento(
            exencion=exencion,
            archivo=archivo,
            es_subsanacion=True,
            estado="PENDIENTE",
        )
        try:
            doc.full_clean()
            doc.save()
            guardados += 1
        except Exception as e:
            messages.error(request, str(e))

    if guardados > 0:
        messages.success(request, f"Se agregaron {guardados} archivo(s).")
    else:
        messages.error(request, "No se pudo subir ningún archivo. Revisá los errores.")

    return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)


# ============================================================
# CONFIRMAR ENVÍO SUBSANACIÓN
# ============================================================
@login_required(login_url="/usuarios/login/")
def confirmar_documento_subsanado_exencion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)
    if exencion.user != request.user:
        return redirect("usuarios:panel_usuario")

    if request.method != "POST":
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    qs = ExencionDocumento.objects.filter(
        exencion=exencion,
        es_subsanacion=True,
        estado="PENDIENTE",
    )

    if not qs.exists():
        messages.error(request, "No hay documentación pendiente para enviar.")
        return redirect("exencion:subir_documento_subsanado_exencion", exencion_id=exencion.id)

    ahora = timezone.now()
    qs.update(estado="ENVIADO", fecha_envio=ahora)

    ObservacionAdministrativaExencion.objects.filter(
        exencion=exencion, subsanada=False
    ).update(subsanada=True)

    exencion.estado = "ENVIADA"
    exencion.save(update_fields=["estado"])

    messages.success(request, "Subsanación enviada correctamente.")
    return redirect("usuarios:panel_usuario")


# ============================================================
# PADRÓN PÚBLICO (QR) + EXCEL (interno)
# ============================================================

def padron_publico_exenciones(request):
    """
    Padrón público (para QR): SOLO aprobadas.
    Sin links, sin admin, sin datos sensibles.
    """
    q = (request.GET.get("q") or "").strip()

    qs = Exencion.objects.filter(
        estado="APROBADA"
    ).order_by("-fecha_emision", "-fecha_creacion")

    if q:
        qs = qs.filter(
            Q(cuit__icontains=q) |
            Q(nombre_razon_social__icontains=q)
        )

    rows = []
    for ex in qs:
        rows.append({
            "id": ex.id,
            "nombre_razon_social": ex.nombre_razon_social or "",
            "cuit": ex.cuit or "",
            "fecha_emision": ex.fecha_emision,
            "fecha_vencimiento": ex.fecha_vencimiento,
            "estado": ex.estado or "",
        })

    return render(request, "exencion/padron_publico_exenciones.html", {
        "q": q,
        "rows": rows,
    })


@staff_member_required
def padron_exenciones_excel(request):
    """
    Excel COMPLETO (interno) con TODOS los campos del modelo Exencion.
    Exporta SOLO aprobadas.
    """
    q = (request.GET.get("q") or "").strip()

    qs = Exencion.objects.filter(
        estado="APROBADA"
    ).order_by("-fecha_emision", "-fecha_creacion")

    if q:
        qs = qs.filter(
            Q(cuit__icontains=q) |
            Q(nombre_razon_social__icontains=q)
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Exenciones Aprobadas"

    def fmt_value(v):
        if v is None:
            return ""
        try:
            return timezone.localtime(v).strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        try:
            return v.strftime("%d/%m/%Y")
        except Exception:
            pass
        try:
            if hasattr(v, "name"):  # FileField
                return v.name or ""
        except Exception:
            pass
        return str(v)

    field_names = [getattr(f, "attname", f.name) for f in Exencion._meta.fields]
    ws.append(field_names)

    for obj in qs:
        ws.append([fmt_value(getattr(obj, n, "")) for n in field_names])

    for col_idx, h in enumerate(field_names, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(len(str(h)) + 2, 14), 45)

    filename = "padron_exenciones_aprobadas_completo.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@staff_member_required
def ir_a_padron_publico_exenciones(request):
    padron = get_object_or_404(PadronPublicoExencion, activo=True)
    return redirect("exencion:padron_publico_exenciones", token=padron.token)
