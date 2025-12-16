# exencion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from convocatorias.models import Convocatoria

from .models import Exencion, ExencionDocumento
from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from .utils import datos_fiscales_completos
from django.contrib import messages


# PASO 1 — INICIAR SOLICITUD
@login_required
def iniciar_solicitud(request, convocatoria_id=None):

    convocatoria = None
    if convocatoria_id is not None:
        convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)

    user = request.user

    # Verificar registro audiovisual
    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    if not (persona_humana or persona_juridica):
        return redirect("/registro/seleccionar-tipo/?next=/exencion/iniciar/")

    persona = persona_humana or persona_juridica

    # ✅ VALIDACIÓN FISCAL ANTES DE CREAR LA EXENCIÓN
    if not datos_fiscales_completos(persona):
        messages.error(
            request,
            "Para solicitar la exención debés completar TODOS los datos fiscales en tu Registro Audiovisual "
            "(Situación IVA, Actividad DGR, Domicilio fiscal, Localidad fiscal y Código postal fiscal)."
        )

        # Redirigir al formulario correcto según el tipo
        if persona_humana:
            return redirect("/registro/persona-humana/")
        else:
            return redirect("/registro/persona-juridica/")

    # ✅ Crear o recuperar solicitud de Exención (ya con datos fiscales completos)
    exencion, creada = Exencion.objects.get_or_create(
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




# PASO 2 — SUBIR DOCUMENTACIÓN
@login_required
def subir_documentacion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)

    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    # 👉 ACA DEFINIMOS LA PERSONA (HUMANA O JURÍDICA)
    persona = exencion.persona_humana or exencion.persona_juridica

    # 👉 VALIDACIÓN DE DATOS FISCALES
    if not datos_fiscales_completos(persona):
        messages.error(
            request,
            "Para solicitar la exención debés completar todos los datos fiscales en tu registro."
        )
        return redirect("/registro/seleccionar-tipo/")

    # --------------------------------------------------
    # SI PASA LA VALIDACIÓN, RECIÉN AHÍ SE PUEDE SUBIR
    # --------------------------------------------------
    if request.method == "POST" and request.FILES.getlist("archivos"):

        for archivo in request.FILES.getlist("archivos"):
            ExencionDocumento.objects.create(
                exencion=exencion,
                archivo=archivo
            )

        exencion.estado = "ENVIADA"
        exencion.save(update_fields=["estado"])

        return redirect("exencion:completada", exencion_id=exencion.id)

    return render(request, "exencion/documentacion.html", {
        "exencion": exencion,
        "convocatoria": exencion.convocatoria,
    })

# PASO 3 — CONFIRMACIÓN FINAL
@login_required
def solicitud_completada(request, exencion_id):
    exencion = get_object_or_404(Exencion, id=exencion_id)

    # Seguridad: solo el dueño puede verla
    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    return render(
        request,
        "exencion/completada.html",
        {
            "exencion": exencion,
            "convocatoria": exencion.convocatoria,
        }
    )

