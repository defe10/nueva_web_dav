from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import PersonaHumanaForm, PersonaJuridicaForm
from .models import PersonaHumana, PersonaJuridica


# ============================================================
# 1. SELECCIONAR TIPO
# ============================================================

def seleccionar_tipo_registro(request):
    if request.method == "POST":
        tipo = request.POST.get("tipo")

        if tipo == "humana":
            return redirect("registro:editar_persona_humana")

        if tipo == "juridica":
            return redirect("registro:editar_persona_juridica")

    return render(request, "registro/seleccionar_tipo.html")


# ============================================================
# 2. PERSONA HUMANA
# ============================================================

def editar_persona_humana(request):
    if request.method == "POST":
        form = PersonaHumanaForm(request.POST)

        if form.is_valid():
            persona = form.save()

            return redirect(
                reverse("registro:inscripcion_exitosa") + f"?tipo=humana&id={persona.id}"
            )

    else:
        form = PersonaHumanaForm()

    return render(
        request,
        "registro/editar_persona_humana.html",
        {"form": form}
    )


# ============================================================
# 3. PERSONA JURÍDICA
# ============================================================

def editar_persona_juridica(request):
    if request.method == "POST":
        form = PersonaJuridicaForm(request.POST)

        if form.is_valid():
            persona = form.save()

            return redirect(
                reverse("registro:inscripcion_exitosa") + f"?tipo=juridica&id={persona.id}"
            )

    else:
        form = PersonaJuridicaForm()

    return render(
        request,
        "registro/editar_persona_juridica.html",
        {"form": form}
    )


# ============================================================
# 4. INSCRIPCIÓN EXITOSA
# ============================================================

def inscripcion_exitosa(request):
    tipo = request.GET.get("tipo")
    id_persona = request.GET.get("id")

    persona = None

    if tipo == "humana":
        persona = PersonaHumana.objects.filter(id=id_persona).first()

    elif tipo == "juridica":
        persona = PersonaJuridica.objects.filter(id=id_persona).first()

    context = {
        "tipo": tipo,
        "persona": persona,
    }

    return render(request, "registro/inscripcion_exitosa.html", context)
