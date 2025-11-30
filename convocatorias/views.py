from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .models import PostulacionIDEA, DocumentoPersonal, DocumentoProyecto
from .forms import PostulacionIdeaForm


# =====================================================
# HOME DE CONVOCATORIAS
# =====================================================

def convocatorias_home(request):
    return render(request, "convocatorias/convocatorias_home.html")


# =====================================================
# VISTAS DE LÍNEAS DEL PLAN IDEA
# =====================================================
# Concursos
def idea_concurso_ficcion(request):
    return render(request, "convocatorias/idea_concurso_ficcion.html")

def idea_concurso_videoclip(request):
    return render(request, "convocatorias/idea_concurso_videoclip.html")


# Programas
def idea_programa_largometrajes(request):
    return render(request, "convocatorias/idea_programa_largometrajes.html")

def idea_programa_laboratorio(request):
    return render(request, "convocatorias/idea_programa_laboratorio.html")

def idea_programa_comunidad(request):
    return render(request, "convocatorias/idea_programa_comunidad.html")

def idea_programa_animacion(request):
    return render(request, "convocatorias/idea_programa_animacion.html")

def idea_programa_videojuegos(request):
    return render(request, "convocatorias/idea_programa_videojuegos.html")


# Subsidios
def idea_subsidio_rodaje(request):
    return render(request, "convocatorias/idea_subsidio_rodaje.html")

def idea_subsidio_finalizacion(request):
    return render(request, "convocatorias/idea_subsidio_finalizacion.html")

def idea_subsidio_eventos(request):
    return render(request, "convocatorias/idea_subsidio_eventos.html")


# Cursos IDEA (opcional)
def idea_curso_presupuestos(request):
    return render(request, "convocatorias/idea_curso_presupuestos.html")

def idea_curso_contar(request):
    return render(request, "convocatorias/idea_curso_contar.html")


# =====================================================
# POSTULACIÓN IDEA
# =====================================================

@login_required
def postular_idea(request):

    # Verificar registro audiovisual
    perfil_h = PersonaHumana.objects.filter(user=request.user).first()
    perfil_j = PersonaJuridica.objects.filter(user=request.user).first()

    # Si no tiene registro → enviarlo a completarlo
    if not perfil_h and not perfil_j:
        return redirect("/registro/seleccionar-tipo/?next=/convocatorias/idea/postular/")

    # Si tiene registro → puede postular
    if request.method == "POST":
        form = PostulacionIdeaForm(request.POST)
        if form.is_valid():
            postulacion = form.save(commit=False)
            postulacion.usuario = request.user
            postulacion.save()
            return redirect("subir_documentacion_personal")
    else:
        form = PostulacionIdeaForm()

    return render(request, "convocatorias/postulacion_idea.html", {"form": form})


# =====================================================
# DOCUMENTACIÓN PERSONAL
# =====================================================

@login_required
def subir_documentacion_personal(request):
    if request.method == "POST" and request.FILES.getlist("archivos"):
        for archivo in request.FILES.getlist("archivos"):
            DocumentoPersonal.objects.create(user=request.user, archivo=archivo)

        return redirect("panel_usuario")

    return render(request, "convocatorias/subir_documentacion_personal.html")


# =====================================================
# DOCUMENTACIÓN PROYECTO
# =====================================================

@login_required
def subir_documentacion_proyecto(request, postulacion_id):
    postulacion = get_object_or_404(PostulacionIDEA, id=postulacion_id)

    if postulacion.usuario != request.user:
        return redirect("inicio")

    if request.method == "POST" and request.FILES.getlist("archivos"):
        for archivo in request.FILES.getlist("archivos"):
            DocumentoProyecto.objects.create(postulacion=postulacion, archivo=archivo)

        return redirect("confirmar_postulacion_idea", postulacion_id=postulacion.id)

    return render(request, "convocatorias/subir_documentacion_proyecto.html", {
        "postulacion": postulacion
    })


# =====================================================
# CONFIRMAR POSTULACIÓN
# =====================================================

@login_required
def confirmar_postulacion_idea(request, postulacion_id):
    postulacion = get_object_or_404(PostulacionIDEA, id=postulacion_id)

    if postulacion.usuario != request.user:
        return redirect("inicio")

    docs_personales = DocumentoPersonal.objects.filter(user=request.user)
    docs_proyecto = DocumentoProyecto.objects.filter(postulacion=postulacion)

    if request.method == "POST":
        postulacion.estado = "ENVIADA"
        postulacion.save()
        return redirect("postulacion_idea_confirmada")

    return render(request, "convocatorias/confirmar_postulacion_idea.html", {
        "postulacion": postulacion,
        "docs_personales": docs_personales,
        "docs_proyecto": docs_proyecto,
    })


# =====================================================
# POSTULACIÓN ENVIADA
# =====================================================

def postulacion_idea_confirmada(request):
    return render(request, "convocatorias/postulacion_idea_confirmada.html")
