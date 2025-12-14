# exencion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from convocatorias.models import Convocatoria
from .models import Exencion, ExencionDocumento
from registro_audiovisual.models import PersonaHumana, PersonaJuridica


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

    # Crear o recuperar solicitud de Exención
    exencion, creada = Exencion.objects.get_or_create(
        user=user,
        convocatoria=convocatoria,
        defaults={
            "persona_humana": persona_humana,
            "persona_juridica": persona_juridica,
            "nombre_razon_social": getattr(
                persona, "nombre_completo",
                getattr(persona, "razon_social", "")
            ),
            "email": getattr(persona, "email", user.email),
            "cuit": getattr(persona, "cuil_cuit", ""),
            "domicilio_fiscal": getattr(persona, "domicilio_fiscal", ""),
            "actividad_dgr": getattr(persona, "actividad_dgr", ""),
        }
    )

    return redirect("exencion:documentacion", exencion_id=exencion.id)



# PASO 2 — SUBIR DOCUMENTACIÓN
@login_required
def subir_documentacion(request, exencion_id):

    exencion = get_object_or_404(Exencion, id=exencion_id)

    if exencion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    # Manejo de subida de archivos
    if request.method == "POST" and request.FILES.getlist("archivos"):

        for archivo in request.FILES.getlist("archivos"):
            ExencionDocumento.objects.create(
                exencion=exencion,    # <— YA ESTÁ CORRECTO
                archivo=archivo
            )

        exencion.estado = "ENVIADA"
        exencion.save()

        return redirect("exencion:completada", exencion_id=exencion.id)

    return render(request, "exencion/documentacion.html", {
        "exencion": exencion,
        "convocatoria": exencion.convocatoria,
    })



# PASO 3 — CONFIRMACIÓN FINAL
@login_required
def solicitud_completada(request, exencion_id):
    exencion = get_object_or_404(Exencion, id=exencion_id)
    return render(request, "exencion/completada.html", {
        "exencion": exencion,
        "convocatoria": exencion.convocatoria,
    })
