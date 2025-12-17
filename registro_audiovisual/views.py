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
    if request.method == "POST":
        tipo = request.POST.get("tipo")

        if tipo == "humana":
            return redirect("registro_audiovisual:editar_persona_humana")

        if tipo == "juridica":
            return redirect("registro_audiovisual:editar_persona_juridica")

    return render(request, "registro/seleccionar_tipo.html")


# ============================================================
# 2. PERSONA HUMANA — CREAR / EDITAR
# ============================================================

@login_required(login_url="/usuarios/login/")
def editar_persona_humana(request):
    user = request.user

    persona_existente = PersonaHumana.objects.filter(user=user).first()

    if request.method == "POST":
        form = PersonaHumanaForm(request.POST, instance=persona_existente)

        if form.is_valid():
            persona = form.save()
            persona.user = user
            persona.save(update_fields=["user"])

            return redirect(
                reverse("registro_audiovisual:inscripcion_exitosa")
                + f"?tipo=humana&id={persona.id}"
            )

    else:
        form = PersonaHumanaForm(instance=persona_existente)  # 👈 SIN initial

    return render(
        request,
        "registro/editar_persona_humana.html",
        {"form": form}
    )





# ============================================================
# 3. PERSONA JURÍDICA — CREAR / EDITAR
# ============================================================

@login_required(login_url="/usuarios/login/")
def editar_persona_juridica(request):
    user = request.user

    persona_existente = PersonaJuridica.objects.filter(user=user).first()

    if request.method == "POST":
        form = PersonaJuridicaForm(request.POST, instance=persona_existente)

        if form.is_valid():
            persona = form.save()
            persona.user = user
            persona.save(update_fields=["user"])

            return redirect(
                reverse("registro_audiovisual:inscripcion_exitosa")
                + f"?tipo=juridica&id={persona.id}"
            )

    else:
        form = PersonaJuridicaForm(instance=persona_existente)  # 👈 SIN initial

    return render(
        request,
        "registro/editar_persona_juridica.html",
        {"form": form}
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

