# convocatorias/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .models import (
    PostulacionIDEA,
    DocumentoPersonal,
    DocumentoProyecto,
    Convocatoria,
    InscripcionCurso
)
from .forms import PostulacionIDEAForm, ConvocatoriaForm


# ============================================================
# HOME
# ============================================================
def convocatorias_home(request):
    return render(request, "convocatorias/convocatoria_home.html", {
        "fomento":    Convocatoria.objects.filter(linea="fomento").order_by("orden"),
        "formacion":  Convocatoria.objects.filter(linea="formacion").order_by("orden"),
        "beneficio":  Convocatoria.objects.filter(linea="beneficio").order_by("orden"),
        "incentivo":  Convocatoria.objects.filter(linea="incentivo").order_by("orden"),
    })


# ============================================================
# INSCRIBIRSE A UNA CONVOCATORIA
# ============================================================
@login_required
def inscribirse_convocatoria(request, slug):

    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    linea = convocatoria.linea.lower()

    # --------------------------------------
    # CASO 1: FORMACIÓN → inscripción simple
    # --------------------------------------
    if linea == "formacion":

        inscripcion, creada = InscripcionCurso.objects.get_or_create(
            user=request.user,
            convocatoria=convocatoria
        )

        return render(request, "convocatorias/inscripcion_curso_completada.html", {
            "convocatoria": convocatoria,
            "creada": creada,
        })

    # --------------------------------------
    # CASO 2: FOMENTO → formulario IDEA
    # --------------------------------------
    if linea == "fomento":
        return redirect("convocatorias:postular_convocatoria",
                        convocatoria_id=convocatoria.id)

   # BENEFICIO → EXENCIÓN (nuevo flujo)
    if convocatoria.linea == "beneficio":
        return redirect("exencion:solicitar_exencion", convocatoria_id=convocatoria.id)

    # INCENTIVO → sigue usando IDEA
    if convocatoria.linea == "incentivo":
        return redirect("convocatorias:postular_convocatoria", convocatoria_id=convocatoria.id)

    # Si no coincide, volvemos al detalle
    return redirect("convocatorias:convocatoria_detalle", slug=slug)



# ============================================================
# POSTULAR A CONVOCATORIA (FORMULARIO)
# ============================================================
@login_required(login_url="/usuarios/login/")
def postular_convocatoria(request, convocatoria_id):

    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)
    linea = convocatoria.linea.lower()
    user = request.user

    # ----------------------------
    # Validar registro audiovisual
    # ----------------------------
    tiene_h = PersonaHumana.objects.filter(user=user).exists()
    tiene_j = PersonaJuridica.objects.filter(user=user).exists()

    if not (tiene_h or tiene_j):
        return redirect(
            f"/registro/seleccionar-tipo/?next=/convocatorias/{convocatoria.slug}/inscribirse/"
        )

    # ============================================================
    # SOLO FOMENTO, BENEFICIO E INCENTIVO USAN FORMULARIO IDEA
    # ============================================================
    if linea in ["fomento", "beneficio", "incentivo"]:

        FormClass = PostulacionIDEAForm

        if request.method == "POST":
            form = FormClass(request.POST)
            if form.is_valid():
                postulacion = form.save(commit=False)
                postulacion.user = user
                postulacion.convocatoria = convocatoria
                postulacion.estado = "ENVIADA"
                postulacion.save()

                return redirect("convocatorias:subir_documentacion_proyecto",
                                postulacion_id=postulacion.id)

        else:
            form = FormClass()

        return render(request, "convocatorias/postulacion_formulario.html", {
            "convocatoria": convocatoria,
            "form": form
        })

    # ============================================================
    # FORMACIÓN → Nunca debería llegar acá
    # ============================================================
    return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)



# ============================================================
# DOCUMENTACIÓN PERSONAL
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documentacion_personal(request, postulacion_id):

    postulacion = get_object_or_404(PostulacionIDEA, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method == "POST" and request.FILES.getlist("archivos"):

        for archivo in request.FILES.getlist("archivos"):
            DocumentoPersonal.objects.create(
                user=request.user,
                archivo=archivo
            )

        return redirect("convocatorias:subir_documentacion_proyecto",
                        postulacion_id=postulacion.id)

    return render(request, "convocatorias/documentacion_personal.html", {
        "postulacion": postulacion
    })


# ============================================================
# DOCUMENTACIÓN PROYECTO
# ============================================================
@login_required
def subir_documentacion_proyecto(request, postulacion_id):

    postulacion = get_object_or_404(PostulacionIDEA, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method == "POST" and request.FILES.getlist("archivos"):

        for archivo in request.FILES.getlist("archivos"):
            DocumentoProyecto.objects.create(
                postulacion=postulacion,
                archivo=archivo
            )

        return redirect("convocatorias:postulacion_confirmada",
                        postulacion_id=postulacion.id)

    return render(request, "convocatorias/documentacion_proyecto.html", {
        "postulacion": postulacion
    })


# ============================================================
# CONFIRMACIÓN FINAL
# ============================================================
def postulacion_confirmada(request, postulacion_id):

    postulacion = get_object_or_404(PostulacionIDEA, id=postulacion_id)
    return render(request, "convocatorias/postulacion_completada.html", {
        "postulacion": postulacion,
        "convocatoria": postulacion.convocatoria,
    })


# ============================================================
# CREAR CONVOCATORIA
# ============================================================
@staff_member_required
def crear_convocatoria(request):
    if request.method == "POST":
        form = ConvocatoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("convocatorias:convocatorias_home")
    else:
        form = ConvocatoriaForm()

    return render(request, "convocatorias/convocatoria_crear.html", {"form": form})


# ============================================================
# DETALLE
# ============================================================
def convocatoria_detalle(request, slug):
    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    return render(request, "convocatorias/convocatoria_detalle.html", {
        "convocatoria": convocatoria
    })


@login_required
def documentacion_completada(request):
    return render(request, "convocatorias/documentacion_completada.html")
