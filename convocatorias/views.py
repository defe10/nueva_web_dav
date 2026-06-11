from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from convocatorias.models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
    DocumentoIntegrante,
    IntegrantePostulacion,
    InscripcionFormacion,
    Rendicion,
)

from .forms import (
    PostulacionForm,
    ConvocatoriaForm,
    InscripcionFormacionForm,
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
    hoy = timezone.localdate()

    # ✅ bloqueo por fechas
    if hoy < convocatoria.fecha_inicio:
        messages.error(request, "La convocatoria todavía no se encuentra abierta.")
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

    if hoy > convocatoria.fecha_fin:
        messages.error(request, "La convocatoria ya finalizó.")
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

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

            form.instance.user = request.user
            form.instance.convocatoria = convocatoria

            if form.is_valid():
                obj = form.save(commit=False)

                if persona_humana:
                    obj.persona_humana = persona_humana
                    obj.persona_juridica = None
                elif persona_juridica:
                    obj.persona_juridica = persona_juridica
                    obj.persona_humana = None

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



# ============================================================
# WIZARD DE POSTULACIÓN — NUEVO FLUJO
# ============================================================

PASOS_INTEGRANTES = {
    "director":  "DIRECTOR",
    "guionista": "GUIONISTA",
    "realizador": "REALIZADOR",
}

DOCS_PROYECTO_CONFIG = [
    ("GUION",                 "mostrar_guion",                "Guion"),
    ("DOSSIER",               "mostrar_dossier",              "Dossier del proyecto"),
    ("MATERIAL_ADICIONAL",    "mostrar_material_adicional",   "Material adicional"),
    ("PLANILLA_OFICIAL",      "mostrar_planilla_oficial",     "Planilla oficial"),
    ("REGISTRO_DNDA",         "mostrar_dnda",                 "Registro DNDA"),
    ("AUTORIZACION_DERECHOS", "mostrar_autorizacion_derechos","Autorización de derechos"),
    ("NOTA_INTENCION",        "mostrar_nota_intencion",       "Nota de intención / documentación"),
    ("CARTA_INTENCION",       "mostrar_carta_intencion",      "Carta de intención"),
    ("CONSTANCIA_INVITACION", "mostrar_constancia_invitacion","Constancia de invitación/participación"),
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
        return None


def _docs_proyecto_activos(config):
    """Retorna lista de (tipo, label) según la configuración de la convocatoria."""
    if not config:
        return []
    return [
        (tipo, label)
        for tipo, attr, label in DOCS_PROYECTO_CONFIG
        if getattr(config, attr, False)
    ]


# ── Inicio: crea o recupera el borrador y redirige al paso 1 ──────────────────
@login_required(login_url="/usuarios/login/")
def wizard_inicio(request, convocatoria_id):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_id)

    persona_humana = _get_persona_productor(request.user)
    if not persona_humana:
        messages.error(request, "Debés completar tu Registro Audiovisual antes de postularte.")
        return redirect("registro_audiovisual:mi_registro")

    postulacion = Postulacion.objects.filter(
        user=request.user,
        convocatoria=convocatoria,
        estado="borrador",
    ).first()

    if not postulacion:
        postulacion = Postulacion.objects.create(
            user=request.user,
            convocatoria=convocatoria,
            estado="borrador",
        )
        IntegrantePostulacion.objects.create(
            postulacion=postulacion,
            rol="PRODUCTOR",
            persona_humana=persona_humana,
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
    integrante = postulacion.integrantes.filter(rol="PRODUCTOR").first()

    requiere_cbu = bool(config and config.requiere_cbu)
    form = ProductorCBUForm(instance=postulacion, requiere_cbu=requiere_cbu)

    if request.method == "POST":
        form = ProductorCBUForm(request.POST, instance=postulacion, requiere_cbu=requiere_cbu)
        if form.is_valid():
            form.save()
            paso_sig = ctx["paso_siguiente"]
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=paso_sig)

    ctx.update({
        "persona":      persona,
        "integrante":   integrante,
        "form":         form,
        "requiere_cbu": requiere_cbu,
        "docs_dni":     integrante.documentos.filter(tipo="DNI").first() if integrante else None,
        "docs_arca":    integrante.documentos.filter(tipo="CONSTANCIA_ARCA").first() if integrante else None,
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
                defaults={"archivo": archivo},
            )
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── Pasos 2/3/4: Integrante (director, guionista, realizador) ─────────────────
def _paso_integrante(request, postulacion, config, ctx, rol):
    label = dict(IntegrantePostulacion.ROLES).get(rol, rol)
    integrante = postulacion.integrantes.filter(rol=rol).first()
    form = IntegranteSearchForm()
    resultados = []
    buscado = False

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "buscar":
            form = IntegranteSearchForm(request.POST)
            if form.is_valid():
                nombre = form.cleaned_data["nombre_busqueda"]
                resultados = PersonaHumana.objects.filter(nombre_completo__icontains=nombre)[:10]
                buscado = True

        elif accion == "seleccionar":
            persona_id = request.POST.get("persona_id")
            persona = get_object_or_404(PersonaHumana, pk=persona_id)
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

    ctx.update({
        "rol":        rol,
        "label":      label,
        "integrante": integrante,
        "form":       form,
        "resultados": resultados,
        "buscado":    buscado,
        "docs_dni":   integrante.documentos.filter(tipo="DNI").first() if integrante else None,
        "docs_arca":  integrante.documentos.filter(tipo="CONSTANCIA_ARCA").first() if integrante else None,
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

        elif accion == "siguiente":
            return redirect("convocatorias:wizard_paso", postulacion_id=postulacion.id, paso=ctx["paso_siguiente"])

    docs_subidos = {
        tipo: postulacion.documentos.filter(tipo=tipo)
        for tipo, _ in docs_activos
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
            postulacion.declaracion_jurada = True
            postulacion.estado = "enviado"
            postulacion.fecha_envio = timezone.now()

            # Marcar todos los documentos pendientes como enviados
            postulacion.documentos.filter(estado="PENDIENTE").update(
                estado="ENVIADO",
                fecha_envio=timezone.now(),
            )
            postulacion.integrantes.prefetch_related("documentos")
            for integrante in postulacion.integrantes.all():
                integrante.documentos.filter(estado="PENDIENTE").update(
                    estado="ENVIADO",
                    fecha_envio=timezone.now(),
                )

            postulacion.save()
            return redirect("convocatorias:postulacion_confirmada", postulacion_id=postulacion.id)

    # Resumen para mostrar antes de confirmar
    persona = _get_persona_productor(request.user)
    integrantes = postulacion.integrantes.select_related("persona_humana").exclude(rol="PRODUCTOR")
    docs_activos = _docs_proyecto_activos(config)
    docs_subidos = {
        tipo: postulacion.documentos.filter(tipo=tipo)
        for tipo, _ in docs_activos
    }

    ctx.update({
        "form":        form,
        "persona":     persona,
        "integrantes": integrantes,
        "docs_activos": docs_activos,
        "docs_subidos": docs_subidos,
    })
    return render(request, "convocatorias/wizard/paso_confirmacion.html", ctx)
