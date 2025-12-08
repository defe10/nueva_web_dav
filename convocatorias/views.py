from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone   # <-- IMPORT NECESARIO

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .models import PostulacionIDEA, DocumentoPersonal, DocumentoProyecto, Convocatoria
from .forms import PostulacionIdeaForm, ConvocatoriaForm
from django.contrib.admin.views.decorators import staff_member_required


# =====================================================
# HOME DE CONVOCATORIAS
# =====================================================

def convocatorias_home(request):

    idea = Convocatoria.objects.filter(
        categoria__in=["CONCURSO", "PROGRAMA", "SUBSIDIO"]
    ).order_by("orden")

    cursos = Convocatoria.objects.filter(
        categoria="CURSO"
    ).order_by("orden")

    incentivos = Convocatoria.objects.filter(
        categoria__in=["INCENTIVO", "BENEFICIO"]
    ).order_by("orden")

    return render(request, "convocatorias/convocatorias_home.html", {
        "idea": idea,
        "cursos": cursos,
        "incentivos": incentivos,
    })






# =====================================================
# POSTULACIÓN IDEA
# =====================================================

@login_required
def postular_idea(request):

    # Verificar registro audiovisual
    perfil_h = PersonaHumana.objects.filter(user=request.user).first()
    perfil_j = PersonaJuridica.objects.filter(user=request.user).first()

    if not perfil_h and not perfil_j:
        return redirect("/registro/seleccionar-tipo/?next=/convocatorias/idea/postular/")

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
        return redirect("seleccionar_tipo_registro")

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
            DocumentoProyecto.objects.create(
                postulacion=postulacion,
                archivo=archivo
            )
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


# DEL FORMULARIO WEB CONVOCATORIA

@staff_member_required
def crear_convocatoria(request):
    if request.method == "POST":
        form = ConvocatoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("convocatorias_home")
    else:
        form = ConvocatoriaForm()

    return render(request, "convocatorias/crear_convocatoria.html", {
        "form": form
    })


# Formulario dinamico


def convocatoria_detalle(request, slug):
    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    return render(request, "convocatorias/detalle_convocatoria.html", {
        "convocatoria": convocatoria
    })
