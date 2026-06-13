from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required


from .forms import PersonaHumanaForm, PersonaJuridicaForm
from .models import PersonaHumana, PersonaJuridica


# ============================================================
# 1. SELECCIONAR TIPO DE REGISTRO
# ============================================================

@login_required(login_url="/usuarios/login/")
def seleccionar_tipo_registro(request):
    next_url = request.GET.get("next", "") or request.POST.get("next", "")

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        suffix = f"?next={next_url}" if next_url else ""

        if tipo == "humana":
            return redirect(reverse("registro_audiovisual:editar_persona_humana") + suffix)

        if tipo == "juridica":
            return redirect(reverse("registro_audiovisual:editar_persona_juridica") + suffix)

    return render(request, "registro/seleccionar_tipo.html", {"next_url": next_url})


# ============================================================
# 2. PERSONA HUMANA — CREAR / EDITAR
# ============================================================

@login_required(login_url="/usuarios/login/")
def editar_persona_humana(request):
    user = request.user
    persona_existente = PersonaHumana.objects.filter(user=user).first()
    next_url = request.GET.get("next", "") or request.POST.get("next", "")

    if request.method == "POST":
        form = PersonaHumanaForm(request.POST, instance=persona_existente)

        if form.is_valid():
            persona = form.save()
            persona.user = user
            persona.save(update_fields=["user"])

            if next_url:
                return redirect(next_url)
            return redirect(
                reverse("registro_audiovisual:inscripcion_exitosa")
                + f"?tipo=humana&id={persona.id}"
            )

    else:
        initial = {} if persona_existente else {"email": user.email}
        form = PersonaHumanaForm(instance=persona_existente, initial=initial)

    return render(
        request,
        "registro/editar_persona_humana.html",
        {"form": form, "next_url": next_url}
    )





# ============================================================
# 3. PERSONA JURÍDICA — CREAR / EDITAR
# ============================================================

@login_required(login_url="/usuarios/login/")
def editar_persona_juridica(request):
    user = request.user
    persona_existente = PersonaJuridica.objects.filter(user=user).first()
    next_url = request.GET.get("next", "") or request.POST.get("next", "")

    if request.method == "POST":
        form = PersonaJuridicaForm(request.POST, instance=persona_existente)

        if form.is_valid():
            persona = form.save()
            persona.user = user
            persona.save(update_fields=["user"])

            if next_url:
                return redirect(next_url)
            return redirect(
                reverse("registro_audiovisual:inscripcion_exitosa")
                + f"?tipo=juridica&id={persona.id}"
            )

    else:
        initial = {} if persona_existente else {"email": user.email}
        form = PersonaJuridicaForm(instance=persona_existente, initial=initial)

    return render(
        request,
        "registro/editar_persona_juridica.html",
        {"form": form, "next_url": next_url}
    )



# ============================================================
# 4. INSCRIPCIÓN EXITOSA (GENÉRICA)
# ============================================================

@login_required(login_url="/usuarios/login/")
def inscripcion_exitosa(request):
    tipo = request.GET.get("tipo")
    id_persona = request.GET.get("id")

    persona = None

    if tipo == "humana":
        persona = PersonaHumana.objects.filter(id=id_persona).first()

    elif tipo == "juridica":
        persona = PersonaJuridica.objects.filter(id=id_persona).first()

    return render(
        request,
        "registro/inscripcion_exitosa.html",
        {
            "tipo": tipo,
            "persona": persona,
        }
    )


# ============================================================
# 5. CONFIRMAR / ACTUALIZAR DATOS ANTES DE UN TRÁMITE
# ============================================================

@login_required(login_url="/usuarios/login/")
def confirmar_datos(request):
    user = request.user
    next_url = request.GET.get("next", "")

    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    if not (persona_humana or persona_juridica):
        suffix = f"?next={next_url}" if next_url else ""
        return redirect(reverse("registro_audiovisual:seleccionar_tipo_registro") + suffix)

    persona = persona_humana or persona_juridica
    tipo = "humana" if persona_humana else "juridica"

    edit_view = (
        "registro_audiovisual:editar_persona_humana"
        if persona_humana
        else "registro_audiovisual:editar_persona_juridica"
    )
    # Después de editar, vuelve a confirmar_datos para que el usuario pueda continuar
    confirmar_url = reverse("registro_audiovisual:confirmar_datos")
    if next_url:
        confirmar_url += f"?next={next_url}"
    edit_url = reverse(edit_view) + f"?next={confirmar_url}"

    return render(request, "registro/confirmar_datos.html", {
        "persona": persona,
        "tipo": tipo,
        "next_url": next_url,
        "edit_url": edit_url,
    })

