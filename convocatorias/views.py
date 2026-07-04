from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from convocatorias.models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
    DocumentoIntegrante,
    IntegrantePostulacion,
    Rendicion,
)

from .forms import (
    PostulacionForm,
    ConvocatoriaForm,
    MiembroJuradoFormSet,
    CriterioEvaluacionFormSet,
    ConfiguracionPostulacionForm,
    ProductorCBUForm,
    IntegranteSearchForm,
    ProyectoDataForm,
    DocumentoProyectoForm,
    DocumentoIntegranteForm,
    DeclaracionJuradaForm,
)

# ============================================================
# LÍMITES DE ARCHIVOS POR POSTULACIÓN
# ============================================================

MAX_DOCS_POR_TIPO = {
    # Genéricos (flujo viejo / línea libre)
    "PERSONAL":  5,
    "PROYECTO":  3,
    "SUBSANADO": 3,
    # Productor
    "COMPROBANTE_CBU": 1,
    # Documentos del proyecto (1 archivo por tipo)
    "GUION":                 1,
    "DOSSIER":               1,
    "MATERIAL_ADICIONAL":    1,
    "PLANILLA_OFICIAL":      1,
    "REGISTRO_DNDA":         1,
    "AUTORIZACION_DERECHOS": 1,
    "NOTA_INTENCION":        1,
    "CARTA_INTENCION":       1,
    "CONSTANCIA_INVITACION": 1,
    "DOCUMENTACION":         5,
    # Persona jurídica
    "ESTATUTO":              1,
    "CONSTANCIA_ARCA_JUR":   1,
    "DNI_REPRESENTANTE":     1,
    "DNI_PRODUCTOR_RESP":    1,
    "ACTA_AUTORIDADES":      1,
    "CONTRATO_COPRODUCTORA": 1,
}

TIPO_LABEL = {
    "PERSONAL":  "personal",
    "PROYECTO":  "del proyecto",
    "SUBSANADO": "de subsanación",
    "COMPROBANTE_CBU":       "comprobante de CBU",
    "GUION":                 "guion",
    "DOSSIER":               "dossier",
    "MATERIAL_ADICIONAL":    "material adicional",
    "PLANILLA_OFICIAL":      "planilla oficial",
    "REGISTRO_DNDA":         "registro DNDA",
    "AUTORIZACION_DERECHOS": "autorización de derechos",
    "NOTA_INTENCION":        "nota de intención",
    "CARTA_INTENCION":       "carta de intención",
    "CONSTANCIA_INVITACION": "constancia de invitación",
}


def _validar_cupo_documentos(postulacion, tipo, cantidad_nueva):
    """
    Valida cupo TOTAL por tipo (PENDIENTE + ENVIADO).
    Tipos no listados en MAX_DOCS_POR_TIPO son rechazados.
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

        # solo las que ya terminaron
        cerradas = base.filter(fecha_fin__lt=hoy)

        return vigentes, cerradas

    vigentes = qs.filter(fecha_inicio__lte=hoy, fecha_fin__gte=hoy)
    cerradas = qs.filter(fecha_fin__lt=hoy)

    return render(
        request,
        "convocatorias/convocatoria_home.html",
        {
            "hoy": hoy,
            "vigentes": vigentes,
            "cerradas": cerradas,
        },
    )


# ============================================================
# INSCRIBIRSE A UNA CONVOCATORIA
# ============================================================
def inscribirse_convocatoria(request, slug):
    convocatoria = get_object_or_404(Convocatoria, slug=slug)
    linea = (convocatoria.linea or "").lower()
    hoy = timezone.localdate()

    if not request.user.is_authenticated:
        messages.warning(request, "Para inscribirte en una convocatoria necesitás ingresar con tu usuario.")
        return redirect(f"/usuarios/login/?next={request.path}")

    # ✅ bloqueo por fechas
    if hoy < convocatoria.fecha_inicio:
        messages.error(request, "La convocatoria todavía no se encuentra abierta.")
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

    if hoy > convocatoria.fecha_fin:
        messages.error(request, "La convocatoria ya finalizó.")
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

    # ========================================================
    # FOMENTO / CASH REBATE — flujo IDEA
    # ========================================================
    if linea in ["fomento", "cash_rebate"]:
        persona_humana = PersonaHumana.objects.filter(user=request.user).first()
        persona_juridica = PersonaJuridica.objects.filter(user=request.user).first()
        postular_url = reverse("convocatorias:postular_convocatoria", kwargs={"convocatoria_id": convocatoria.id})

        if not (persona_humana or persona_juridica):
            messages.warning(request, "Para postularte a esta convocatoria primero debés completar tu Registro Audiovisual.")
            return redirect(reverse("registro_audiovisual:seleccionar_tipo_registro") + f"?next={postular_url}")

        # Validar tipo de postulante según configuración
        config = getattr(convocatoria, "configuracion", None)
        if config:
            tipo = config.tipo_postulante
            if tipo == "HUMANA" and not persona_humana:
                messages.error(request, "Esta convocatoria es solo para personas humanas. Debés completar tu registro como persona humana.")
                return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)
            elif tipo == "JURIDICA" and not persona_juridica:
                messages.error(request, "Esta convocatoria es solo para personas jurídicas. Debés completar tu registro como empresa/institución.")
                return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

        if not request.GET.get("confirmed"):
            return redirect(reverse("registro_audiovisual:confirmar_datos") + f"?next={postular_url}")
        return redirect(postular_url)

    # ========================================================
    # EXENCIÓN IMPOSITIVA
    # ========================================================
    if linea == "exencion":
        return redirect(
            "exencion:iniciar_convocatoria",
            convocatoria_id=convocatoria.id,
        )

    return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)




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
        return redirect(request.META.get("HTTP_REFERER", "/"))

    postulacion_id = documento.postulacion.id
    tipo = documento.tipo
    documento.delete()
    messages.success(request, "Documento eliminado.")

    if tipo == "SUBSANADO":
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion_id)

    return redirect(request.META.get("HTTP_REFERER", "/"))







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
        config_form = ConfiguracionPostulacionForm(request.POST, request.FILES)
        jurado_formset = MiembroJuradoFormSet(request.POST, request.FILES)
        criterio_formset = CriterioEvaluacionFormSet(request.POST)
        if form.is_valid() and config_form.is_valid() and jurado_formset.is_valid() and criterio_formset.is_valid():
            convocatoria = form.save()
            config = config_form.save(commit=False)
            config.convocatoria = convocatoria
            config.save()
            jurado_formset.instance = convocatoria
            jurado_formset.save()
            criterio_formset.instance = convocatoria
            criterio_formset.save()
            return redirect("convocatorias:convocatorias_home")
    else:
        form = ConvocatoriaForm()
        config_form = ConfiguracionPostulacionForm()
        jurado_formset = MiembroJuradoFormSet()
        criterio_formset = CriterioEvaluacionFormSet()

    return render(request, "convocatorias/convocatoria_crear.html", {
        "form": form,
        "config_form": config_form,
        "jurado_formset": jurado_formset,
        "criterio_formset": criterio_formset,
    })


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
    postulacion = get_object_or_404(Postulacion, id=postulacion_id, user=request.user)

    if request.method != "POST":
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    # ✅ NUEVO: exigir al menos 1 doc subsanado cargado (pendiente o enviado)
    if not DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="SUBSANADO",
    ).exists():
        messages.error(request, "Debés subir al menos un archivo antes de enviar la subsanación.")
        return redirect("convocatorias:subir_documento_subsanado", postulacion_id=postulacion.id)

    qs_pendientes = DocumentoPostulacion.objects.filter(
        postulacion=postulacion,
        tipo="SUBSANADO",
        estado="PENDIENTE",
    )

    if not qs_pendientes.exists():
        messages.info(request, "Tu documentación subsanada ya fue enviada.")
        return redirect("usuarios:panel_usuario")

    ahora = timezone.now()
    qs_pendientes.update(estado="ENVIADO", fecha_envio=ahora)

    postulacion.estado = "revision_admin"
    postulacion.save(update_fields=["estado"])

    messages.success(request, "La documentación subsanada fue enviada correctamente.")
    return redirect("usuarios:panel_usuario")



# ============================================================
# RENDICIÓN — DETALLE Y ENVÍO (link)
# ============================================================
@login_required(login_url="/usuarios/login/")
def rendicion_detalle(request, rendicion_id):
    rendicion = get_object_or_404(Rendicion, id=rendicion_id, user=request.user)

    postulacion = rendicion.postulacion
    convocatoria = postulacion.convocatoria

    CAMPOS_IMPACTO = [
        ("honorarios_tecnicos",     "Honorarios técnicos"),
        ("honorarios_elenco",       "Honorarios elenco"),
        ("otros_honorarios",        "Otros honorarios"),
        ("insumos",                 "Insumos"),
        ("servicios_audiovisuales", "Servicios audiovisuales"),
        ("servicios_logistica",     "Servicios / logística"),
    ]

    if request.method == "POST":
        accion = request.POST.get("accion", "guardar")
        link = (request.POST.get("link_documentacion") or "").strip()
        obs  = (request.POST.get("observaciones_usuario") or "").strip()

        rendicion.link_documentacion  = link
        rendicion.observaciones_usuario = obs

        # Planilla xlsx
        if "planilla_xlsx" in request.FILES:
            rendicion.planilla_xlsx = request.FILES["planilla_xlsx"]

        # Montos impacto económico
        for campo, _ in CAMPOS_IMPACTO:
            try:
                rendicion.__setattr__(campo, request.POST.get(campo) or 0)
            except (ValueError, TypeError):
                pass

        if accion == "enviar":
            if not link and not rendicion.planilla_xlsx:
                messages.error(request, "Subí la planilla o agregá un link antes de enviar.")
                rendicion.save()
                return redirect("convocatorias:rendicion_detalle", rendicion_id=rendicion.id)
            rendicion.estado = "ENVIADO"
            rendicion.save()
            messages.success(request, "Rendición enviada correctamente.")
            return redirect("usuarios:panel_usuario")

        rendicion.save()
        messages.success(request, "Borrador guardado.")
        return redirect("convocatorias:rendicion_detalle", rendicion_id=rendicion.id)

    return render(
        request,
        "convocatorias/rendicion_detalle.html",
        {
            "rendicion":     rendicion,
            "postulacion":   postulacion,
            "convocatoria":  convocatoria,
            "campos_impacto": CAMPOS_IMPACTO,
        },
    )



# ============================================================
# WIZARD DE POSTULACIÓN — NUEVO FLUJO
# ============================================================

PASOS_INTEGRANTES = {
    "director":  "DIRECTOR",
    "guionista": "GUIONISTA",
    "realizador": "REALIZADOR",
}

# (tipo, attr_config, label, obligatorio)
DOCS_PROYECTO_CONFIG = [
    ("GUION",                 "mostrar_guion",                "Guion",                               True),
    ("DOSSIER",               "mostrar_dossier",              "Dossier del proyecto",                True),
    ("PLANILLA_OFICIAL",      "mostrar_planilla_oficial",     "Planilla oficial",                    True),
    ("REGISTRO_DNDA",         "mostrar_dnda",                 "Registro DNDA",                       True),
    ("CONSTANCIA_INVITACION", "mostrar_constancia_invitacion","Constancia de invitación/participación", True),
    ("NOTA_INTENCION",        "mostrar_nota_intencion",       "Nota de intención",                   True),
    ("DOCUMENTACION",         "mostrar_documentacion",        "Documentación",                       True),
    ("MATERIAL_ADICIONAL",    "mostrar_material_adicional",   "Material adicional",                  False),
    ("AUTORIZACION_DERECHOS", "mostrar_autorizacion_derechos","Autorización de derechos",            False),
]


def _get_pasos(config):
    pasos = ["productor"]
    if config:
        if config.requiere_director:
            pasos.append("director")
        if config.requiere_guionista:
            pasos.append("guionista")
        if config.requiere_realizador:
            pasos.append("realizador")
    pasos += ["proyecto", "documentacion", "confirmacion"]
    return pasos


def _get_persona_productor(user):
    try:
        return user.persona_humana
    except PersonaHumana.DoesNotExist:
        pass
    try:
        return user.persona_juridica
    except PersonaJuridica.DoesNotExist:
        return None


def _docs_proyecto_activos(config):
    """Retorna lista de (tipo, label, obligatorio) según la configuración de la convocatoria."""
    if not config:
        return []
    return [
        (tipo, label, obligatorio)
        for tipo, attr, label, obligatorio in DOCS_PROYECTO_CONFIG
        if getattr(config, attr, False)
    ]


# ── Inicio: crea o recupera el borrador y redirige al paso 1 ──────────────────
@login_required(login_url="/usuarios/login/")
def wizard_inicio(request, convocatoria_id):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_id)
    config = getattr(convocatoria, "configuracion", None)
    tipo_postulante = config.tipo_postulante if config else "HUMANA"

    persona_humana = PersonaHumana.objects.filter(user=request.user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=request.user).first()

    if tipo_postulante == "HUMANA":
        persona = persona_humana
        if not persona:
            messages.error(request, "Esta convocatoria es solo para personas humanas. Debés completar tu registro antes de postularte.")
            return redirect("registro_audiovisual:seleccionar_tipo_registro")
    elif tipo_postulante == "JURIDICA":
        persona = persona_juridica
        if not persona:
            messages.error(request, "Esta convocatoria es solo para personas jurídicas. Debés completar tu registro como empresa/institución.")
            return redirect("registro_audiovisual:seleccionar_tipo_registro")
    else:  # AMBAS
        persona = persona_humana or persona_juridica
        if not persona:
            messages.error(request, "Debés completar tu Registro Audiovisual antes de postularte.")
            return redirect("registro_audiovisual:seleccionar_tipo_registro")

    postulacion = Postulacion.objects.filter(
        user=request.user,
        convocatoria=convocatoria,
        estado="borrador",
    ).first()

    if not postulacion:
        with transaction.atomic():
            postulacion = Postulacion.objects.create(
                user=request.user,
                convocatoria=convocatoria,
                estado="borrador",
            )
            IntegrantePostulacion.objects.create(
                postulacion=postulacion,
                rol="PRODUCTOR",
                persona_humana=persona if isinstance(persona, PersonaHumana) else None,
                verificado=True,
            )

    config = getattr(convocatoria, "configuracion", None)
    pasos = _get_pasos(config)
    return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=pasos[0])


# ── Router principal ──────────────────────────────────────────────────────────
@login_required(login_url="/usuarios/login/")
def wizard_paso(request, postulacion_id, paso):
    postulacion = get_object_or_404(Postulacion, pk=postulacion_id, user=request.user)

    if postulacion.estado == "enviado":
        return redirect("convocatorias:postulacion_confirmada", postulacion_id=postulacion.id)

    convocatoria = postulacion.convocatoria
    config = getattr(convocatoria, "configuracion", None)
    pasos = _get_pasos(config)

    if paso not in pasos:
        return redirect("convocatorias:wizard_paso", postulacion_id=postulacion_id, paso=pasos[0])

    idx = pasos.index(paso)
    ctx = {
        "postulacion":    postulacion,
        "convocatoria":   convocatoria,
        "config":         config,
        "pasos":          pasos,
        "paso_actual":    paso,
        "paso_num":       idx + 1,
        "total_pasos":    len(pasos),
        "paso_siguiente": pasos[idx + 1] if idx + 1 < len(pasos) else None,
        "paso_anterior":  pasos[idx - 1] if idx > 0 else None,
    }

    handlers = {
        "productor":    _paso_productor,
        "proyecto":     _paso_proyecto,
        "documentacion":_paso_documentacion,
        "confirmacion": _paso_confirmacion,
    }
    # Pasos de integrantes (director, guionista, realizador)
    for nombre_paso, rol in PASOS_INTEGRANTES.items():
        handlers[nombre_paso] = lambda req, post, cfg, c, _rol=rol: _paso_integrante(req, post, cfg, c, _rol)

    return handlers[paso](request, postulacion, config, ctx)


# ── Paso 1: Productor ─────────────────────────────────────────────────────────
def _paso_productor(request, postulacion, config, ctx):
    persona = _get_persona_productor(request.user)

    # Garantizar que el productor tiene su IntegrantePostulacion para poder subir docs
    nombre_productor = ""
    if persona:
        nombre_productor = getattr(persona, "nombre_completo", None) or getattr(persona, "razon_social", "")

    integrante, _ = IntegrantePostulacion.objects.get_or_create(
        postulacion=postulacion,
        rol="PRODUCTOR",
        defaults={
            "persona_humana": persona if isinstance(persona, PersonaHumana) else None,
            "nombre_busqueda": nombre_productor,
            "verificado": True,
        },
    )

    requiere_cbu = bool(config and config.requiere_cbu)
    form = ProductorCBUForm(instance=postulacion, requiere_cbu=requiere_cbu)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "subir_cbu_doc":
            cbu_val = request.POST.get("cbu", "").strip()
            if cbu_val:
                postulacion.cbu = cbu_val
                postulacion.save(update_fields=["cbu"])
            archivo = request.FILES.get("archivo")
            if archivo:
                DocumentoPostulacion.objects.update_or_create(
                    postulacion=postulacion,
                    tipo="COMPROBANTE_CBU",
                    defaults={"archivo": archivo, "estado": "ENVIADO"},
                )
            return redirect(
                reverse("convocatorias:wizard_paso", kwargs={"postulacion_id": postulacion.id, "paso": ctx["paso_actual"]}) + "#docs"
            )

        form = ProductorCBUForm(request.POST, instance=postulacion, requiere_cbu=requiere_cbu)
        if form.is_valid():
            form.save()
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_siguiente"])

    es_juridica = isinstance(persona, PersonaJuridica)
    requiere_productor_responsable = es_juridica and bool(config and config.requiere_productor_responsable)

    def doc(tipo):
        return integrante.documentos.filter(tipo=tipo).first() if integrante else None

    ctx.update({
        "persona":      persona,
        "integrante":   integrante,
        "form":         form,
        "requiere_cbu": requiere_cbu,
        "es_juridica":  es_juridica,
        "requiere_productor_responsable": requiere_productor_responsable,
        # docs persona humana
        "docs_dni":     doc("DNI"),
        "docs_arca":    doc("CONSTANCIA_ARCA"),
        "docs_cv":      doc("CV_BIOFILMOGRAFIA"),
        # docs persona jurídica
        "docs_estatuto":          doc("ESTATUTO"),
        "docs_arca_jur":          doc("CONSTANCIA_ARCA_JUR"),
        "docs_dni_representante": doc("DNI_REPRESENTANTE"),
        "docs_dni_productor":     doc("DNI_PRODUCTOR_RESP"),
        "docs_acta":              doc("ACTA_AUTORIDADES"),
        "docs_contrato":          doc("CONTRATO_COPRODUCTORA"),
        # comprobante CBU (ambos tipos)
        "docs_cbu":     postulacion.documentos.filter(tipo="COMPROBANTE_CBU").first() if requiere_cbu else None,
    })
    return render(request, "convocatorias/wizard/paso_productor.html", ctx)


# ── Subir documento de integrante (DNI o ARCA) — POST único ──────────────────
@login_required(login_url="/usuarios/login/")
def subir_doc_integrante(request, postulacion_id, rol):
    postulacion = get_object_or_404(Postulacion, pk=postulacion_id, user=request.user)
    integrante = get_object_or_404(IntegrantePostulacion, postulacion=postulacion, rol=rol.upper())

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        archivo = request.FILES.get("archivo")
        if tipo and archivo:
            DocumentoIntegrante.objects.update_or_create(
                integrante=integrante,
                tipo=tipo,
                defaults={"archivo": archivo, "estado": "ENVIADO"},
            )
        else:
            messages.error(request, "No se recibió ningún archivo. Intentá de nuevo.")
    referer = request.META.get("HTTP_REFERER", "/")
    sep = "&" if "?" in referer else "#"
    return redirect(referer.split("#")[0] + "#docs")


# ── Pasos 2/3/4: Integrante (director, guionista, realizador) ─────────────────
def _paso_integrante(request, postulacion, config, ctx, rol):
    label = dict(IntegrantePostulacion.ROLES).get(rol, rol)
    integrante = postulacion.integrantes.filter(rol=rol).first()
    form = IntegranteSearchForm()
    resultados = []
    buscado = False

    # El guionista nunca requiere documentación
    mostrar_docs = (rol != "GUIONISTA")

    # Para director: si la config permite coincidir con productor, ofrecemos
    # la opción de usar la misma PersonaHumana del productor
    puede_coincidir_con_productor = (
        rol == "DIRECTOR"
        and config
        and config.director_puede_coincidir
    )
    persona_productor = None
    if puede_coincidir_con_productor:
        integrante_prod = postulacion.integrantes.filter(rol="PRODUCTOR").first()
        persona_productor = integrante_prod.persona_humana if integrante_prod else None

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "usar_productor" and persona_productor:
            integrante, _ = IntegrantePostulacion.objects.update_or_create(
                postulacion=postulacion,
                rol=rol,
                defaults={
                    "persona_humana": persona_productor,
                    "nombre_busqueda": persona_productor.nombre_completo,
                    "verificado": True,
                },
            )
            messages.success(request, f"{label} establecido como el mismo que el productor/a.")
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_actual"])

        elif accion == "buscar":
            form = IntegranteSearchForm(request.POST)
            if form.is_valid():
                nombre = form.cleaned_data["nombre_busqueda"]
                if len(nombre) < 3:
                    messages.error(request, "Ingresá al menos 3 caracteres para buscar.")
                    buscado = True
                else:
                    resultados = PersonaHumana.objects.filter(
                        Q(nombre__icontains=nombre) | Q(apellido__icontains=nombre)
                    )[:10]
                    buscado = True

        elif accion == "seleccionar":
            persona_id = request.POST.get("persona_id")
            persona = get_object_or_404(PersonaHumana, pk=persona_id)

            # Validar que el director no sea el mismo que el productor si no está habilitado
            if rol == "DIRECTOR" and not (config and config.director_puede_coincidir):
                integrante_prod = postulacion.integrantes.filter(rol="PRODUCTOR").first()
                if integrante_prod and integrante_prod.persona_humana == persona:
                    messages.error(request, "En esta convocatoria el/la director/a debe ser una persona distinta al/a la productor/a presentante.")
                    buscado = True
                    resultados = PersonaHumana.objects.filter(nombre_completo__icontains=persona.nombre_completo)[:10]
                    ctx.update({
                        "rol": rol, "label": label, "integrante": integrante,
                        "form": form, "resultados": resultados, "buscado": buscado,
                        "mostrar_docs": mostrar_docs,
                        "puede_coincidir_con_productor": puede_coincidir_con_productor,
                        "persona_productor": persona_productor,
                        "docs_dni": None, "docs_arca": None, "docs_cv": None,
                    })
                    return render(request, "convocatorias/wizard/paso_integrante.html", ctx)

            integrante, _ = IntegrantePostulacion.objects.update_or_create(
                postulacion=postulacion,
                rol=rol,
                defaults={
                    "persona_humana": persona,
                    "nombre_busqueda": persona.nombre_completo,
                    "verificado": True,
                },
            )
            messages.success(request, f"{label} vinculado: {persona.nombre_completo}")
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_actual"])

        elif accion == "siguiente":
            if not integrante or not integrante.verificado:
                messages.error(request, f"Debés buscar y seleccionar al/a la {label} antes de continuar.")
            else:
                return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_siguiente"])

    # Si el integrante es la misma persona que el productor, reusar sus docs
    es_mismo_que_productor = False
    integrante_productor = None
    if integrante and integrante.persona_humana and mostrar_docs:
        integrante_prod = postulacion.integrantes.filter(rol="PRODUCTOR").first()
        if integrante_prod and integrante_prod.persona_humana == integrante.persona_humana:
            es_mismo_que_productor = True
            integrante_productor = integrante_prod

    if es_mismo_que_productor and integrante_productor:
        docs_dni  = integrante_productor.documentos.filter(tipo="DNI").first()
        docs_arca = integrante_productor.documentos.filter(tipo="CONSTANCIA_ARCA").first()
        docs_cv   = integrante_productor.documentos.filter(tipo="CV_BIOFILMOGRAFIA").first()
    else:
        docs_dni  = integrante.documentos.filter(tipo="DNI").first() if integrante and mostrar_docs else None
        docs_arca = integrante.documentos.filter(tipo="CONSTANCIA_ARCA").first() if integrante and mostrar_docs else None
        docs_cv   = integrante.documentos.filter(tipo="CV_BIOFILMOGRAFIA").first() if integrante and mostrar_docs else None

    ctx.update({
        "rol":                       rol,
        "label":                     label,
        "integrante":                integrante,
        "form":                      form,
        "resultados":                resultados,
        "buscado":                   buscado,
        "mostrar_docs":              mostrar_docs,
        "puede_coincidir_con_productor": puede_coincidir_con_productor,
        "persona_productor":         persona_productor,
        "es_mismo_que_productor":    es_mismo_que_productor,
        "docs_dni":                  docs_dni,
        "docs_arca":                 docs_arca,
        "docs_cv":                   docs_cv,
    })
    return render(request, "convocatorias/wizard/paso_integrante.html", ctx)


# ── Paso Proyecto ─────────────────────────────────────────────────────────────
def _paso_proyecto(request, postulacion, config, ctx):
    form = ProyectoDataForm(instance=postulacion, config=config)

    if request.method == "POST":
        form = ProyectoDataForm(request.POST, instance=postulacion, config=config)
        if form.is_valid():
            form.save()
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_siguiente"])

    ctx["form"] = form
    return render(request, "convocatorias/wizard/paso_proyecto.html", ctx)


# ── Paso Documentación del proyecto ──────────────────────────────────────────
def _paso_documentacion(request, postulacion, config, ctx):
    docs_activos = _docs_proyecto_activos(config)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "subir":
            tipo = request.POST.get("tipo")
            archivo = request.FILES.get("archivo")
            if tipo and archivo:
                ok, msg = _validar_cupo_documentos(postulacion, tipo, 1)
                if ok:
                    DocumentoPostulacion.objects.create(
                        postulacion=postulacion,
                        tipo=tipo,
                        archivo=archivo,
                    )
                else:
                    messages.error(request, msg)
            return redirect(
                reverse("convocatorias:wizard_paso", kwargs={"postulacion_id": postulacion.id, "paso": ctx["paso_actual"]}) + "#docs"
            )

        elif accion == "siguiente":
            faltantes = [
                label for tipo, label, obligatorio in docs_activos
                if obligatorio and not postulacion.documentos.filter(tipo=tipo).exists()
            ]
            if faltantes:
                for label in faltantes:
                    messages.error(request, f"Falta subir: {label}")
            else:
                return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_siguiente"])

    docs_subidos = {
        tipo: list(postulacion.documentos.filter(tipo=tipo))
        for tipo, _, _obl in docs_activos
    }

    ctx.update({
        "docs_activos": docs_activos,
        "docs_subidos": docs_subidos,
    })
    return render(request, "convocatorias/wizard/paso_documentacion.html", ctx)


# ── Paso Confirmación + DDJJ ──────────────────────────────────────────────────
def _paso_confirmacion(request, postulacion, config, ctx):
    form = DeclaracionJuradaForm()

    if request.method == "POST":
        form = DeclaracionJuradaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                ahora = timezone.now()
                postulacion.declaracion_jurada = True
                postulacion.estado = "enviado"
                postulacion.fecha_envio = ahora
                postulacion.save()

                postulacion.documentos.filter(estado="PENDIENTE").update(
                    estado="ENVIADO",
                    fecha_envio=ahora,
                )
                for integrante in postulacion.integrantes.all():
                    integrante.documentos.filter(estado="PENDIENTE").update(
                        estado="ENVIADO",
                        fecha_envio=ahora,
                    )

            return redirect("convocatorias:postulacion_confirmada", postulacion_id=postulacion.id)

    # Resumen para mostrar antes de confirmar
    persona = _get_persona_productor(request.user)
    integrantes = postulacion.integrantes.select_related("persona_humana").exclude(rol="PRODUCTOR")
    docs_activos = _docs_proyecto_activos(config)
    docs_subidos = {
        tipo: list(postulacion.documentos.filter(tipo=tipo))
        for tipo, _, _obl in docs_activos
    }

    ctx.update({
        "form":        form,
        "persona":     persona,
        "integrantes": integrantes,
        "docs_activos": docs_activos,
        "docs_subidos": docs_subidos,
    })
    return render(request, "convocatorias/wizard/paso_confirmacion.html", ctx)


# ============================================================
# DESCARGA DE PLANILLA OFICIAL PRE-COMPLETADA
# ============================================================

@login_required
def descargar_planilla_oficial(request, postulacion_id):
    from django.http import HttpResponse
    from convocatorias.planilla_generator import generar_planilla_postulacion

    postulacion = get_object_or_404(Postulacion, id=postulacion_id, user=request.user)

    try:
        xlsx_bytes, filename = generar_planilla_postulacion(postulacion)
    except (ValueError, FileNotFoundError) as e:
        messages.error(request, str(e))
        return redirect(
            reverse("convocatorias:wizard_paso", args=[postulacion_id, "documentacion"])
        )

    response = HttpResponse(
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# JURADO
# ============================================================
