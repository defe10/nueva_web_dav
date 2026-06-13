from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from convocatorias.models import Convocatoria

from .models import InscripcionFormacion, ConfiguracionInscripcionFormacion
from .forms import (
    InscripcionFormacionForm,
    ConvocatoriaFormacionForm,
    ConfiguracionInscripcionFormacionForm,
)


@login_required
def crear_convocatoria_formacion(request):
    if not request.user.is_staff:
        return redirect("convocatorias:convocatorias_home")

    if request.method == "POST":
        form        = ConvocatoriaFormacionForm(request.POST, request.FILES)
        config_form = ConfiguracionInscripcionFormacionForm(request.POST)

        if form.is_valid() and config_form.is_valid():
            conv          = form.save(commit=False)
            conv.linea    = "formacion"
            conv.categoria = "FORMACION"
            conv.save()

            config = config_form.save(commit=False)
            config.convocatoria = conv
            config.save()

            messages.success(request, "Convocatoria de formación creada correctamente.")
            return redirect("convocatorias:convocatoria_detalle", slug=conv.slug)
    else:
        form        = ConvocatoriaFormacionForm()
        config_form = ConfiguracionInscripcionFormacionForm()

    return render(request, "formacion/crear_convocatoria.html", {
        "form":        form,
        "config_form": config_form,
    })


def inscribirse(request, convocatoria_id):
    convocatoria = get_object_or_404(Convocatoria, pk=convocatoria_id, linea="formacion")

    if not request.user.is_authenticated:
        messages.warning(request, "Para inscribirte en una formación necesitás ingresar con tu usuario.")
        return redirect(f"/usuarios/login/?next={request.path}")

    # Cursos asincrónicos no tienen inscripción
    if convocatoria.tipo_formacion == "ASINCRONICA":
        if convocatoria.url_curso:
            return redirect(convocatoria.url_curso)
        return redirect("convocatorias:convocatoria_detalle", slug=convocatoria.slug)

    persona_humana  = PersonaHumana.objects.filter(user=request.user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=request.user).first()

    # Si requiere registro, solo acepta PersonaHumana
    if convocatoria.tipo_formacion == "INSCRIPCION_REGISTRO":
        next_url = request.path + "?confirmed=1"
        if not persona_humana:
            messages.warning(
                request,
                "Esta convocatoria requiere estar inscripto en el Registro Audiovisual como persona humana. "
                "Completá tu registro antes de continuar."
            )
            return redirect(reverse("registro_audiovisual:seleccionar_tipo_registro") + f"?next={next_url}")

        if not request.GET.get("confirmed"):
            return redirect(reverse("registro_audiovisual:confirmar_datos") + f"?next={next_url}")

    config = getattr(convocatoria, "config_inscripcion_formacion", None)

    inscripcion = InscripcionFormacion.objects.filter(
        user=request.user,
        convocatoria=convocatoria,
    ).first()

    if request.method == "POST":
        form = InscripcionFormacionForm(
            request.POST,
            request.FILES,
            instance=inscripcion,
            persona_humana=persona_humana,
            persona_juridica=persona_juridica,
            config=config,
        )
        form.instance.user        = request.user
        form.instance.convocatoria = convocatoria

        if form.is_valid():
            obj = form.save(commit=False)

            if persona_humana:
                obj.persona_humana  = persona_humana
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

            obj.save()
            messages.success(request, "Tu inscripción fue registrada correctamente.")
            return redirect("usuarios:panel_usuario")
    else:
        form = InscripcionFormacionForm(
            instance=inscripcion,
            persona_humana=persona_humana,
            persona_juridica=persona_juridica,
            config=config,
        )

    return render(
        request,
        "formacion/inscripcion.html",
        {
            "convocatoria":    convocatoria,
            "form":            form,
            "config":          config,
            "persona_humana":  persona_humana,
            "persona_juridica": persona_juridica,
            "usa_datos_registro": bool(persona_humana or persona_juridica),
            "inscripcion":     inscripcion,
        },
    )
