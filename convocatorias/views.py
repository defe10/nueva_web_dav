from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from convocatorias.models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
    AsignacionJuradoConvocatoria,
)

from .forms import PostulacionForm, ConvocatoriaForm, DocumentoSubsanadoForm
from django.contrib import messages
from django.core.exceptions import ValidationError






# ============================================================
# HOME DE CONVOCATORIAS
# ============================================================
def convocatorias_home(request):
    return render(
        request,
        "convocatorias/convocatoria_home.html",
        {
            "fomento": Convocatoria.objects.filter(linea="fomento").order_by("orden"),
            "formacion": Convocatoria.objects.filter(linea="formacion").order_by("orden"),
            "beneficio": Convocatoria.objects.filter(linea="beneficio").order_by("orden"),
            "incentivo": Convocatoria.objects.filter(linea="incentivo").order_by("orden"),
        },
    )


# ============================================================
# INSCRIBIRSE A UNA CONVOCATORIA
# ============================================================
@login_required
def inscribirse_convocatoria(request, slug):

    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    linea = convocatoria.linea.lower()

    # --------------------------------------
    # FORMACIÓN → inscripción directa
    # --------------------------------------
    if linea == "formacion":

        postulacion, creada = Postulacion.objects.get_or_create(
            user=request.user,
            convocatoria=convocatoria,
            defaults={
                "estado": "enviado"
            }
        )

        if creada:
            messages.success(
                request,
                "Tu inscripción fue registrada correctamente."
            )
        else:
            messages.info(
                request,
                "Ya estabas inscripto/a en esta convocatoria."
            )

        return redirect("usuarios:panel_usuario")

    # --------------------------------------
    # FOMENTO + BENEFICIO → IDEA
    # --------------------------------------
    elif linea in ["fomento", "beneficio"]:
        return redirect(
            "convocatorias:postular_convocatoria",
            convocatoria_id=convocatoria.id
        )

    # --------------------------------------
    # INCENTIVO → EXENCIÓN
    # --------------------------------------
    elif linea == "incentivo":
        return redirect(
            "exencion:iniciar_convocatoria",
            convocatoria_id=convocatoria.id
        )

    # --------------------------------------
    # Fallback seguro
    # --------------------------------------
    return redirect(
        "convocatorias:convocatoria_detalle",
        slug=convocatoria.slug
    )




# ============================================================
# POSTULACIÓN – PASO 1 (FORMULARIO IDEA)
# ============================================================
@login_required(login_url="/usuarios/login/")
def postular_convocatoria(request, convocatoria_id):

    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)
    linea = convocatoria.linea.lower()
    user = request.user

    # --------------------------------------
    # Validar registro audiovisual
    # --------------------------------------
    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    if not (persona_humana or persona_juridica):
        messages.info(
            request,
            "Para inscribirse en esta convocatoria, es necesario completar previamente "
            "los datos del Registro Audiovisual. "
            "Una vez finalizado el registro, podrá volver a esta convocatoria y completar su inscripción."
    )
        return redirect(
            f"/registro/seleccionar-tipo/?next=/convocatorias/{convocatoria.slug}/inscribirse/"
        )

    # --------------------------------------
    # Determinar nombre del presentante
    # --------------------------------------
    if persona_humana:
        persona_nombre = persona_humana.nombre_completo
    else:
        persona_nombre = persona_juridica.razon_social

    # --------------------------------------
    # Solo estas líneas usan IDEA
    # --------------------------------------
    if linea not in ["fomento", "beneficio"]:
        return redirect(
            "convocatorias:convocatoria_detalle",
            slug=convocatoria.slug,
        )

    # --------------------------------------
    # Formulario
    # --------------------------------------
    if request.method == "POST":
        form = PostulacionForm(request.POST)
        if form.is_valid():
            postulacion = form.save(commit=False)
            postulacion.user = user
            postulacion.convocatoria = convocatoria
            postulacion.estado = "enviado"
            postulacion.save()

            return redirect(
                "convocatorias:subir_documentacion_personal",
                postulacion_id=postulacion.id,
            )
    else:
        form = PostulacionForm()

    return render(
        request,
        "convocatorias/postulacion_formulario.html",
        {
            "convocatoria": convocatoria,
            "form": form,
            "persona_nombre": persona_nombre,  # ← CLAVE
        },
    )


# ============================================================
# DOCUMENTACIÓN PERSONAL – PASO 2
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documentacion_personal(request, postulacion_id):

    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    # POST: intenta guardar archivos
    if request.method == "POST":
        archivos = request.FILES.getlist("archivos")

        if not archivos:
            messages.error(request, "No se seleccionó ningún archivo.")
            return render(
                request,
                "convocatorias/documentacion_personal.html",
                {"postulacion": postulacion},
            )

        for archivo in archivos:
            documento = DocumentoPostulacion(
                postulacion=postulacion,
                tipo="PERSONAL",
                archivo=archivo,
            )
            try:
                documento.full_clean()  # 🔐 valida PDF + tamaño
                documento.save()
            except ValidationError as e:
                # Mensaje amigable y volvemos a mostrar el mismo formulario (sin redirect loop)
                msg = e.message_dict.get("archivo", ["Error al validar el archivo."])[0]
                messages.error(request, msg)
                return render(
                    request,
                    "convocatorias/documentacion_personal.html",
                    {"postulacion": postulacion},
                )

        # Si todos los archivos pasaron la validación
        return redirect(
            "convocatorias:subir_documentacion_proyecto",
            postulacion_id=postulacion.id,
        )

    # GET: muestra el formulario
    return render(
        request,
        "convocatorias/documentacion_personal.html",
        {"postulacion": postulacion},
    )


# ============================================================
# DOCUMENTACIÓN DEL PROYECTO – PASO 3
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documentacion_proyecto(request, postulacion_id):

    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    # --------------------------------------
    # POST → subir archivos
    # --------------------------------------
    if request.method == "POST":
        archivos = request.FILES.getlist("archivos")

        if not archivos:
            messages.error(request, "No se seleccionó ningún archivo.")
            return render(
                request,
                "convocatorias/documentacion_proyecto.html",
                {"postulacion": postulacion},
            )

        for archivo in archivos:
            documento = DocumentoPostulacion(
                postulacion=postulacion,
                tipo="PROYECTO",  # ✅ correcto
                archivo=archivo,
            )
            try:
                documento.full_clean()  # 🔐 valida PDF + tamaño
                documento.save()
            except ValidationError as e:
                messages.error(
                    request,
                    e.message_dict.get("archivo", ["Error al validar el archivo."])[0]
                )
                return render(
                    request,
                    "convocatorias/documentacion_proyecto.html",
                    {"postulacion": postulacion},
                )

        # --------------------------------------
        # si todo salió bien
        # --------------------------------------
        return redirect(
            "convocatorias:postulacion_confirmada",
            postulacion_id=postulacion.id,
        )

    # --------------------------------------
    # GET → mostrar formulario
    # --------------------------------------
    return render(
        request,
        "convocatorias/documentacion_proyecto.html",
        {"postulacion": postulacion},
    )


# ============================================================
# POSTULACIÓN COMPLETADA – PASO FINAL
# ============================================================
@login_required(login_url="/usuarios/login/")
def postulacion_confirmada(request, postulacion_id):

    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    return render(
        request,
        "convocatorias/postulacion_completada.html",
        {
            "postulacion": postulacion,
            "convocatoria": postulacion.convocatoria,
        },
    )


# ============================================================
# CREAR CONVOCATORIA (ADMIN)
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

    return render(
        request,
        "convocatorias/convocatoria_crear.html",
        {"form": form},
    )


# ============================================================
# DETALLE DE CONVOCATORIA
# ============================================================
def convocatoria_detalle(request, slug):

    convocatoria = get_object_or_404(Convocatoria, slug=slug)

    return render(
        request,
        "convocatorias/convocatoria_detalle.html",
        {
            "convocatoria": convocatoria,
        },
    )

@login_required
def subir_documento_subsanado(request, postulacion_id):
    postulacion = get_object_or_404(
        Postulacion,
        id=postulacion_id,
        user=request.user
    )

    if request.method == "POST":
        form = DocumentoSubsanadoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.postulacion = postulacion
            documento.tipo = "SUBSANADO"
            documento.documento = "SUBSANADO"
            documento.save()

            # 🔁 Cambio de estado
            postulacion.estado = "revision_admin"
            postulacion.save()

            messages.success(
                request,
                "La documentación fue enviada correctamente y se encuentra en revisión administrativa."
            )

            return redirect("usuarios:panel_usuario")
    else:
        form = DocumentoSubsanadoForm()

    return render(
        request,
        "convocatorias/subir_documento_subsanado.html",
        {
            "postulacion": postulacion,
            "form": form
        }
    )



@login_required
def ver_documentacion_proyecto(request, postulacion_id):

    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    documentos = postulacion.documentos.all()

    return render(
        request,
        "convocatorias/ver_documentacion_proyecto.html",
        {
            "postulacion": postulacion,
            "documentos": documentos,
        }
    )
