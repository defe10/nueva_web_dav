from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from convocatorias.models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
    InscripcionFormacion,
    Rendicion,
)

from .forms import (
    PostulacionForm,
    ConvocatoriaForm,
    InscripcionFormacionForm,
)

# ============================================================
# LÍMITES DE ARCHIVOS POR POSTULACIÓN
# ============================================================

MAX_DOCS_POR_TIPO = {
    "PERSONAL": 3,
    "PROYECTO": 3,
    "SUBSANADO": 3,
}

TIPO_LABEL = {
    "PERSONAL": "personal",
    "PROYECTO": "del proyecto",
    "SUBSANADO": "de subsanación",
}


def _validar_cupo_documentos(postulacion, tipo, cantidad_nueva):
    """
    Valida cupo TOTAL por tipo (PENDIENTE + ENVIADO).
    Así garantizamos un máximo absoluto de 3 por tipo.
    """
    maximo = MAX_DOCS_POR_TIPO.get(tipo, 0)

    existentes = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo=tipo,
    ).count()

    if existentes + cantidad_nueva > maximo:
        restantes = max(0, maximo - existentes)
        label = TIPO_LABEL.get(tipo, tipo.lower())
        return False, (
            f"Máximo {maximo} archivos {label}. "
            f"Ya tenés {existentes}. Podés subir {restantes} más."
        )

    return True, ""


# ============================================================
# HOME DE CONVOCATORIAS
# (muestra abiertas + cerradas como histórico)
# ============================================================
def convocatorias_home(request):
    hoy = timezone.now().date()

    qs = Convocatoria.objects.all().order_by("orden", "-fecha_inicio")

    def separar_por_linea(linea):
        base = qs.filter(linea=linea)

        vigentes = base.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)

        # "cerradas" = terminó o todavía no empezó (futuras)
        cerradas = base.filter(Q(fecha_fin__lt=hoy) | Q(fecha_inicio__gt=hoy))

        return vigentes, cerradas

    fomento_vig, fomento_cer = separar_por_linea("fomento")
    formacion_vig, formacion_cer = separar_por_linea("formacion")
    beneficio_vig, beneficio_cer = separar_por_linea("beneficio")
    incentivo_vig, incentivo_cer = separar_por_linea("incentivo")
    libre_vig, libre_cer = separar_por_linea("libre")

    return render(
        request,
        "convocatorias/convocatoria_home.html",
        {
            "hoy": hoy,
            "fomento": fomento_vig,
            "fomento_cerradas": fomento_cer,
            "formacion": formacion_vig,
            "formacion_cerradas": formacion_cer,
            "beneficio": beneficio_vig,
            "beneficio_cerradas": beneficio_cer,
            "incentivo": incentivo_vig,
            "incentivo_cerradas": incentivo_cer,
            "libre": libre_vig,
            "libre_cerradas": libre_cer,
        },
    )


# ============================================================
# INSCRIBIRSE A UNA CONVOCATORIA
# ============================================================
@login_required
def inscribirse_convocatoria(request, slug):
    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    linea = (convocatoria.linea or "").lower()

    # ========================================================
    # FORMACIÓN — inscripción sin obligar Registro Audiovisual
    # ========================================================
    if linea == "formacion":
        persona_humana = PersonaHumana.objects.filter(user=request.user).first()
        persona_juridica = PersonaJuridica.objects.filter(user=request.user).first()

        inscripcion = InscripcionFormacion.objects.filter(
            user=request.user,
            convocatoria=convocatoria
        ).first()

        if request.method == "POST":
            form = InscripcionFormacionForm(
                request.POST,
                instance=inscripcion,
                persona_humana=persona_humana,
                persona_juridica=persona_juridica,
            )

            # ✅ CLAVE: setear FK antes del is_valid()
            form.instance.user = request.user
            form.instance.convocatoria = convocatoria

            if form.is_valid():
                obj = form.save(commit=False)

                # ✅ vincular registro si existe
                if persona_humana:
                    obj.persona_humana = persona_humana
                    obj.persona_juridica = None
                elif persona_juridica:
                    obj.persona_juridica = persona_juridica
                    obj.persona_humana = None

                # ✅ si hay registro: forzar datos desde registro (aunque estén ocultos)
                persona = persona_humana or persona_juridica
                if persona:
                    obj.email = getattr(persona, "email", "") or obj.email or request.user.email or ""
                    obj.telefono = getattr(persona, "telefono", "") or obj.telefono or ""

                    if hasattr(obj, "nombre") and not obj.nombre:
                        obj.nombre = getattr(persona, "nombre", "") or ""
                    if hasattr(obj, "apellido") and not obj.apellido:
                        obj.apellido = getattr(persona, "apellido", "") or ""
                    if hasattr(obj, "dni") and not obj.dni:
                        obj.dni = getattr(persona, "dni", "") or ""

                    if hasattr(obj, "localidad") and not obj.localidad:
                        obj.localidad = getattr(persona, "localidad", None) or getattr(persona, "lugar_residencia", None)

                obj.save()
                messages.success(request, "Tu inscripción fue registrada correctamente.")
                return redirect("usuarios:panel_usuario")
        else:
            form = InscripcionFormacionForm(
                instance=inscripcion,
                persona_humana=persona_humana,
                persona_juridica=persona_juridica,
            )

        return render(
            request,
            "convocatorias/inscripcion_formacion.html",
            {
                "convocatoria": convocatoria,
                "form": form,
                "persona_humana": persona_humana,
                "persona_juridica": persona_juridica,
                "usa_datos_registro": bool(persona_humana or persona_juridica),
            },
        )

    # ========================================================
    # LÍNEA LIBRE — directo a documentación
    # ========================================================
    if linea == "libre":
        postulacion, creada = Postulacion.objects.get_or_create(
            user=request.user,
            convocatoria=convocatoria,
            defaults={"estado": "borrador"}
        )

        if creada:
            messages.success(request, "Tu postulación fue creada. Ahora podés subir la documentación.")
        else:
            messages.info(request, "Ya tenías una postulación iniciada. Podés continuar con la documentación.")

        return redirect(
            "convocatorias:subir_documentacion_personal",
            postulacion_id=postulacion.id,
        )

    # ========================================================
    # FOMENTO / BENEFICIO — flujo IDEA
    # ========================================================
    if linea in ["fomento", "beneficio"]:
        return redirect(
            "convocatorias:postular_convocatoria",
            convocatoria_id=convocatoria.id,
        )

    # ========================================================
    # INCENTIVO — EXENCIÓN
    # ========================================================
    if linea == "incentivo":
        return redirect(
            "exencion:iniciar_convocatoria",
            convocatoria_id=convocatoria.id,
        )

    return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)


# ============================================================
# POSTULACIÓN — PASO 1 (IDEA)
# ============================================================
@login_required(login_url="/usuarios/login/")
def postular_convocatoria(request, convocatoria_id):
    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)
    user = request.user

    # seguridad: solo IDEA
    if (convocatoria.linea or "").lower() not in ["fomento", "beneficio"]:
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

    # validar registro audiovisual
    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    if not (persona_humana or persona_juridica):
        messages.info(request, "Antes de inscribirte es necesario completar el Registro Audiovisual.")
        return redirect(f"/registro/seleccionar-tipo/?next=/convocatorias/{convocatoria.slug}/inscribirse/")

    persona_nombre = (
        persona_humana.nombre_completo
        if persona_humana
        else persona_juridica.razon_social
    )

    if request.method == "POST":
        form = PostulacionForm(request.POST)

        # ✅ CLAVE: setear FK antes del is_valid()
        form.instance.user = user
        form.instance.convocatoria = convocatoria

        if form.is_valid():
            postulacion = form.save(commit=False)

            postulacion.estado = "borrador"

            # ✅ BLINDAJE: evita NULL siempre (PA tiene NOT NULL en DB)
            if not postulacion.fecha_envio:
                postulacion.fecha_envio = timezone.now()

            postulacion.save()

            return redirect(
                "convocatorias:subir_documentacion_personal",
                postulacion_id=postulacion.id,
            )
        else:
            # ✅ Para que se vea el error de "declaracion_jurada" en el template si no tilda
            messages.error(request, "Revisá los campos marcados. La declaración jurada es obligatoria.")
    else:
        form = PostulacionForm()

    return render(
        request,
        "convocatorias/postulacion_formulario.html",
        {
            "convocatoria": convocatoria,
            "form": form,
            "persona_nombre": persona_nombre,
        },
    )


# ============================================================
# DOCUMENTACIÓN PERSONAL (pantalla)
# ============================================================
@login_required(login_url="/usuarios/login/")
def subir_documentacion_personal(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    documentos_pendientes = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PERSONAL",
        estado="PENDIENTE",
    ).order_by("-fecha_subida")

    documentos_enviados = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PERSONAL",
        estado="ENVIADO",
    ).order_by("-fecha_envio", "-fecha_subida")

    return render(
        request,
        "convocatorias/documentacion_personal.html",
        {
            "postulacion": postulacion,
            "documentos_pendientes": documentos_pendientes,
            "documentos_enviados": documentos_enviados,
        },
    )


# ============================================================
# DOCUMENTACIÓN PERSONAL (agregar archivos)
# ============================================================
@login_required(login_url="/usuarios/login/")
def agregar_documentacion_personal(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    archivos = request.FILES.getlist("archivos")
    if not archivos:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    ok, msg = _validar_cupo_documentos(postulacion, "PERSONAL", len(archivos))
    if not ok:
        messages.error(request, msg)
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    for archivo in archivos:
        documento = DocumentoPostulacion(
            postulacion=postulacion,
            tipo="PERSONAL",
            estado="PENDIENTE",
            archivo=archivo,
        )
        try:
            documento.full_clean()
            documento.save()
        except ValidationError as e:
            messages.error(request, e.message_dict.get("archivo", ["Error al validar el archivo."])[0])
            return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    messages.success(request, "Archivos agregados. Podés eliminar o enviar cuando estés listo/a.")
    return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)


# ============================================================
# ELIMINAR DOCUMENTO (sirve para PERSONAL/PROYECTO/SUBSANADO)
# ============================================================
@login_required(login_url="/usuarios/login/")
def eliminar_documento_postulacion(request, documento_id):
    documento = get_object_or_404(DocumentoPostulacion, id=documento_id)

    if documento.postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("convocatorias:convocatorias_home")

    if documento.estado != "PENDIENTE":
        messages.error(request, "No podés eliminar un documento ya enviado.")
        tipo = documento.tipo
        if tipo == "PROYECTO":
            return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=documento.postulacion.id)
        if tipo == "SUBSANADO":
            return redirect("convocatorias:subir_documento_subsanado", postulacion_id=documento.postulacion.id)
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=documento.postulacion.id)

    postulacion_id = documento.postulacion.id
    tipo = documento.tipo
    documento.delete()

    messages.success(request, "Documento eliminado.")

    if tipo == "PERSONAL":
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion_id)
    if tipo == "PROYECTO":
        return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion_id)
    if tipo == "SUBSANADO":
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion_id)

    return redirect("usuarios:panel_usuario")


# ============================================================
# DOCUMENTACIÓN PERSONAL (confirmar envío)
# ============================================================
@login_required(login_url="/usuarios/login/")
def confirmar_documentacion_personal(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    qs = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PERSONAL",
        estado="PENDIENTE",
    )

    if not qs.exists():
        messages.error(request, "No tenés documentos pendientes para enviar.")
        return redirect("convocatorias:subir_documentacion_personal", postulacion_id=postulacion.id)

    ahora = timezone.now()
    qs.update(estado="ENVIADO", fecha_envio=ahora)

    messages.success(request, "Documentación personal enviada correctamente.")
    return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)


# ============================================================
# DOCUMENTACIÓN DEL PROYECTO (pantalla)
# ============================================================
@login_required(login_url="/usuarios/login/")
def confirmar_documentacion_proyecto(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    # Seguridad: solo el dueño
    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    # Solo por POST
    if request.method != "POST":
        return redirect(
            "convocatorias:subir_documentacion_proyecto",
            postulacion_id=postulacion.id
        )

    # Documentos pendientes del proyecto
    qs = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PROYECTO",
        estado="PENDIENTE",
    )

    if not qs.exists():
        messages.error(request, "No tenés documentos pendientes para enviar.")
        return redirect(
            "convocatorias:subir_documentacion_proyecto",
            postulacion_id=postulacion.id
        )

    # Marcar documentos como enviados
    ahora = timezone.now()
    qs.update(
        estado="ENVIADO",
        fecha_envio=ahora,
    )

    # ✅ FINAL REAL DE LA POSTULACIÓN
    postulacion.estado = "enviado"
    postulacion.fecha_envio = ahora
    postulacion.save(update_fields=["estado", "fecha_envio"])

    messages.success(
        request,
        "Documentación del proyecto enviada correctamente. Tu postulación quedó registrada."
    )

    return redirect(
        "convocatorias:postulacion_confirmada",
        postulacion_id=postulacion.id
    )



# ============================================================
# DOCUMENTACIÓN DEL PROYECTO (agregar archivos)
# ============================================================
@login_required(login_url="/usuarios/login/")
def agregar_documentacion_proyecto(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    if request.method != "POST":
        return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)

    archivos = request.FILES.getlist("archivos")
    if not archivos:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)

    ok, msg = _validar_cupo_documentos(postulacion, "PROYECTO", len(archivos))
    if not ok:
        messages.error(request, msg)
        return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)

    for archivo in archivos:
        documento = DocumentoPostulacion(
            postulacion=postulacion,
            tipo="PROYECTO",
            estado="PENDIENTE",
            archivo=archivo,
        )
        try:
            documento.full_clean()
            documento.save()
        except ValidationError as e:
            messages.error(request, e.message_dict.get("archivo", ["Error al validar el archivo."])[0])
            return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)

    messages.success(request, "Archivos agregados. Podés eliminar o enviar cuando estés listo/a.")
    return redirect("convocatorias:subir_documentacion_proyecto", postulacion_id=postulacion.id)





# ============================================================
# POSTULACIÓN CONFIRMADA
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

    return render(request, "convocatorias/convocatoria_crear.html", {"form": form})


# ============================================================
# DETALLE CONVOCATORIA
# ============================================================
def convocatoria_detalle(request, slug):
    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    return render(request, "convocatorias/convocatoria_detalle.html", {"convocatoria": convocatoria})


# ============================================================
# SUBSANADO (pantalla)
# ============================================================
@login_required
def subir_documento_subsanado(request, postulacion_id):
    postulacion = get_object_or_404(
        Postulacion,
        id=postulacion_id,
        user=request.user,
    )

    documentos_pendientes = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="SUBSANADO",
        estado="PENDIENTE",
    ).order_by("-fecha_subida")

    documentos_enviados = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="SUBSANADO",
        estado="ENVIADO",
    ).order_by("-fecha_envio", "-fecha_subida")

    return render(
        request,
        "convocatorias/subir_documento_subsanado.html",
        {
            "postulacion": postulacion,
            "documentos_pendientes": documentos_pendientes,
            "documentos_enviados": documentos_enviados,
        },
    )


# ============================================================
# SUBSANADO (agregar archivos)
# ============================================================
@login_required
def agregar_documento_subsanado(request, postulacion_id):
    postulacion = get_object_or_404(
        Postulacion,
        id=postulacion_id,
        user=request.user,
    )

    if request.method != "POST":
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    archivos = request.FILES.getlist("archivos")
    if not archivos:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    ok, msg = _validar_cupo_documentos(postulacion, "SUBSANADO", len(archivos))
    if not ok:
        messages.error(request, msg)
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    for archivo in archivos:
        documento = DocumentoPostulacion(
            postulacion=postulacion,
            tipo="SUBSANADO",
            estado="PENDIENTE",
            archivo=archivo,
        )
        try:
            documento.full_clean()
            documento.save()
        except ValidationError as e:
            messages.error(request, e.message_dict.get("archivo", ["Error al validar el archivo."])[0])
            return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    messages.success(request, "Archivos agregados. Podés eliminar o enviar cuando estés listo/a.")
    return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)


# ============================================================
# SUBSANADO (confirmar envío)
# ============================================================
@login_required
def confirmar_documento_subsanado(request, postulacion_id):
    postulacion = get_object_or_404(
        Postulacion,
        id=postulacion_id,
        user=request.user,
    )

    if request.method != "POST":
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    qs = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="SUBSANADO",
        estado="PENDIENTE",
    )

    if not qs.exists():
        messages.error(request, "No tenés documentos pendientes para enviar.")
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    ahora = timezone.now()
    qs.update(estado="ENVIADO", fecha_envio=ahora)

    postulacion.estado = "revision_admin"
    postulacion.save()

    messages.success(request, "La documentación subsanada fue enviada correctamente.")
    return redirect("usuarios:panel_usuario")


# ============================================================
# VER DOCUMENTACIÓN
# ============================================================
@login_required
def ver_documentacion_proyecto(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    # ⚠️ seguridad mínima: sólo dueño o staff
    if postulacion.user != request.user and not request.user.is_staff:
        return redirect("convocatorias:convocatorias_home")

    documentos = postulacion.documentos.all()
    return render(
        request,
        "convocatorias/ver_documentacion_proyecto.html",
        {
            "postulacion": postulacion,
            "documentos": documentos,
        },
    )


# ============================================================
# RENDICIÓN — DETALLE Y ENVÍO (link)
# ============================================================
@login_required(login_url="/usuarios/login/")
def rendicion_detalle(request, rendicion_id):
    rendicion = get_object_or_404(Rendicion, id=rendicion_id, user=request.user)

    postulacion = rendicion.postulacion
    convocatoria = postulacion.convocatoria

    if request.method == "POST":
        link = (request.POST.get("link_documentacion") or "").strip()
        obs = (request.POST.get("observaciones_usuario") or "").strip()

        if not link:
            messages.error(request, "Tenés que cargar un link a la documentación.")
            return redirect("convocatorias:rendicion_detalle", rendicion_id=rendicion.id)

        # Guardar campos
        rendicion.link_documentacion = link
        rendicion.observaciones_usuario = obs

        # Pasar a ENVIADO
        rendicion.estado = "ENVIADO"

        try:
            rendicion.full_clean()
            rendicion.save()
        except ValidationError:
            messages.error(request, "Error al guardar la rendición.")
            return redirect("convocatorias:rendicion_detalle", rendicion_id=rendicion.id)

        messages.success(request, "Rendición enviada correctamente.")
        return redirect("usuarios:panel_usuario")

    return render(
        request,
        "convocatorias/rendicion_detalle.html",
        {
            "rendicion": rendicion,
            "postulacion": postulacion,
            "convocatoria": convocatoria,
        },
    )



@login_required(login_url="/usuarios/login/")
def subir_documentacion_proyecto(request, postulacion_id):
    postulacion = get_object_or_404(Postulacion, id=postulacion_id)

    if postulacion.user != request.user:
        return redirect("convocatorias:convocatorias_home")

    documentos_pendientes = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PROYECTO",
        estado="PENDIENTE",
    ).order_by("-fecha_subida")

    documentos_enviados = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="PROYECTO",
        estado="ENVIADO",
    ).order_by("-fecha_envio", "-fecha_subida")

    return render(
        request,
        "convocatorias/documentacion_proyecto.html",
        {
            "postulacion": postulacion,
            "documentos_pendientes": documentos_pendientes,
            "documentos_enviados": documentos_enviados,
        },
    )

