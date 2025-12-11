from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from convocatorias.models import Convocatoria
from .models import ExencionSolicitud, ExencionDocumento
from registro_audiovisual.models import PersonaHumana, PersonaJuridica


# PASO 1: INICIAR SOLICITUD
@login_required
def iniciar_solicitud(request, convocatoria_id):

    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)

    # Validar registro audiovisual
    user = request.user
    tiene_h = PersonaHumana.objects.filter(user=user).exists()
    tiene_j = PersonaJuridica.objects.filter(user=user).exists()

    if not (tiene_h or tiene_j):
        return redirect(f"/registro/seleccionar-tipo/?next=/exencion/iniciar/{convocatoria.id}/")

    # Crear o recuperar solicitud
    solicitud, creada = ExencionSolicitud.objects.get_or_create(
        user=user,
        convocatoria=convocatoria
    )

    return redirect("exencion:documentacion", solicitud_id=solicitud.id)



# PASO 2: SUBIR DOCUMENTACIÓN
@login_required
def subir_documentacion(request, solicitud_id):

    solicitud = get_object_or_404(ExencionSolicitud, id=solicitud_id)

    if solicitud.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method == "POST" and request.FILES.getlist("archivos"):
        for archivo in request.FILES.getlist("archivos"):
            ExencionDocumento.objects.create(
                solicitud=solicitud,
                archivo=archivo
            )

        solicitud.estado = "PENDIENTE"
        solicitud.save()

        return redirect("exencion:completada", solicitud_id=solicitud.id)

    return render(request, "exencion/documentacion.html", {
        "solicitud": solicitud,
        "convocatoria": solicitud.convocatoria
    })



# PASO 3: CONFIRMACIÓN
def solicitud_completada(request, solicitud_id):
    solicitud = get_object_or_404(ExencionSolicitud, id=solicitud_id)
    return render(request, "exencion/completada.html", {
        "solicitud": solicitud,
        "convocatoria": solicitud.convocatoria
    })
