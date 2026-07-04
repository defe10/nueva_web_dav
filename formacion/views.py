from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from .models import (
    ConvocatoriaFormacion,
    InscripcionFormacion,
    ConfiguracionInscripcionFormacion,
)
from .forms import (
    ConvocatoriaFormacionForm,
    MiembroFormadorFormSet,
    ConfiguracionInscripcionFormacionForm,
    InscripcionFormacionForm,
)


def _enviar_email_inscripcion(request, inscripcion):
    user = inscripcion.user
    destinatario = user.email or inscripcion.email
    if not destinatario:
        return
    panel_url = request.build_absolute_uri(reverse("usuarios:panel_usuario"))
    asunto = f"Inscripción registrada: {inscripcion.convocatoria.titulo}"
    texto = (
        f"Tu inscripción a '{inscripcion.convocatoria.titulo}' fue registrada correctamente.\n\n"
        f"Podés seguir el estado desde tu panel: {panel_url}"
    )
    try:
        html = render_to_string(
            "formacion/email_confirmacion_inscripcion.html",
            {"inscripcion": inscripcion, "user": user, "panel_url": panel_url},
        )
        email = EmailMultiAlternatives(
            subject=asunto, body=texto,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[destinatario],
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=True)
    except Exception:
        pass


@login_required
def crear_convocatoria_formacion(request):
    if not request.user.is_staff:
        return redirect("convocatorias:convocatorias_home")

    if request.method == "POST":
        form           = ConvocatoriaFormacionForm(request.POST, request.FILES)
        config_form    = ConfiguracionInscripcionFormacionForm(request.POST)
        formset        = MiembroFormadorFormSet(request.POST, request.FILES)

        if form.is_valid() and config_form.is_valid() and formset.is_valid():
            conv = form.save()

            config = config_form.save(commit=False)
            config.convocatoria = conv
            config.save()

            formset.instance = conv
            formset.save()

            messages.success(request, "Convocatoria de formación creada correctamente.")
            return redirect("formacion:detalle", slug=conv.slug)
    else:
        form        = ConvocatoriaFormacionForm()
        config_form = ConfiguracionInscripcionFormacionForm()
        formset     = MiembroFormadorFormSet()

    return render(request, "formacion/crear_convocatoria.html", {
        "form":        form,
        "config_form": config_form,
        "formset":     formset,
    })


def detalle(request, slug):
    conv = get_object_or_404(ConvocatoriaFormacion, slug=slug)
    return render(request, "formacion/detalle.html", {"convocatoria": conv})


def inscribirse(request, convocatoria_id):
    conv = get_object_or_404(ConvocatoriaFormacion, pk=convocatoria_id)

    # I: ASINCRONICA no requiere login
    if conv.tipo_formacion == "ASINCRONICA":
        if conv.url_curso:
            return redirect(conv.url_curso)
        return redirect("formacion:detalle", slug=conv.slug)

    if not request.user.is_authenticated:
        messages.warning(request, "Para inscribirte en una formación necesitás ingresar con tu usuario.")
        return redirect(f"/usuarios/login/?next={request.path}")

    if not conv.vigente:
        messages.warning(request, "Las inscripciones para esta formación están cerradas.")
        return redirect("formacion:detalle", slug=conv.slug)

    persona_humana   = PersonaHumana.objects.filter(user=request.user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=request.user).first()

    # E: acepta PersonaJuridica también
    if conv.tipo_formacion == "INSCRIPCION_REGISTRO":
        next_url = request.path + "?confirmed=1"
        if not (persona_humana or persona_juridica):
            messages.warning(
                request,
                "Esta convocatoria requiere estar inscripto/a en el Registro Audiovisual. "
                "Completá tu registro antes de continuar."
            )
            return redirect(reverse("registro_audiovisual:seleccionar_tipo_registro") + f"?next={next_url}")

        if not request.GET.get("confirmed"):
            return redirect(reverse("registro_audiovisual:confirmar_datos") + f"?next={next_url}")

    config = getattr(conv, "config_inscripcion", None)

    inscripcion = InscripcionFormacion.objects.filter(
        user=request.user, convocatoria=conv,
    ).first()

    # F: formulario read-only si ya está admitido o no admitido
    estados_finales = ("admitido", "no_admitido")
    if inscripcion and inscripcion.estado in estados_finales:
        messages.info(
            request,
            f"Tu inscripción ya fue procesada (estado: {inscripcion.get_estado_display()}). "
            "No podés modificarla."
        )
        return redirect("usuarios:panel_usuario")

    # H: control de cupo
    if conv.cupo_maximo and not inscripcion:
        inscriptos = InscripcionFormacion.objects.filter(convocatoria=conv).count()
        if inscriptos >= conv.cupo_maximo:
            messages.warning(
                request,
                "Lo sentimos, esta formación ya alcanzó el cupo máximo de inscriptos."
            )
            return redirect("formacion:detalle", slug=conv.slug)

    if request.method == "POST":
        form = InscripcionFormacionForm(
            request.POST, request.FILES,
            instance=inscripcion,
            persona_humana=persona_humana,
            persona_juridica=persona_juridica,
            config=config,
        )
        form.instance.user        = request.user
        form.instance.convocatoria = conv

        if form.is_valid():
            obj = form.save(commit=False)

            if persona_humana:
                obj.persona_humana   = persona_humana
                obj.persona_juridica = None
            elif persona_juridica:
                obj.persona_juridica = persona_juridica
                obj.persona_humana   = None

            persona = persona_humana or persona_juridica
            if persona:
                obj.email    = getattr(persona, "email",    "") or obj.email    or request.user.email or ""
                obj.telefono = getattr(persona, "telefono", "") or obj.telefono or ""
                if not obj.nombre:
                    obj.nombre = getattr(persona, "nombre", "") or ""
                if not obj.apellido:
                    obj.apellido = getattr(persona, "apellido", "") or ""
                if not obj.dni:
                    obj.dni = getattr(persona, "dni", "") or ""
                if not obj.localidad:
                    obj.localidad = (
                        getattr(persona, "localidad",       None)
                        or getattr(persona, "lugar_residencia", None)
                        or ""
                    )

            es_nueva = obj.pk is None
            obj.save()

            # A: email de confirmación solo en inscripción nueva
            if es_nueva:
                _enviar_email_inscripcion(request, obj)

            messages.success(request, "Tu inscripción fue registrada correctamente.")
            return redirect("usuarios:panel_usuario")
    else:
        form = InscripcionFormacionForm(
            instance=inscripcion,
            persona_humana=persona_humana,
            persona_juridica=persona_juridica,
            config=config,
        )

    return render(request, "formacion/inscripcion.html", {
        "convocatoria":     conv,
        "form":             form,
        "config":           config,
        "persona_humana":   persona_humana,
        "persona_juridica": persona_juridica,
        "usa_datos_registro": bool(persona_humana or persona_juridica),
        "inscripcion":      inscripcion,
        "cupo_maximo":      conv.cupo_maximo,
    })
