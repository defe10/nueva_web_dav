from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PersonaHumana, PersonaJuridica
from .forms import PersonaHumanaForm, PersonaJuridicaForm


@login_required
def seleccionar_tipo_registro(request):
    return render(request, "registro_audiovisual/seleccionar_tipo.html")

@login_required
def editar_persona_humana(request):

    perfil = PersonaHumana.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = PersonaHumanaForm(request.POST, instance=perfil)
        if form.is_valid():
            nuevo = form.save(commit=False)
            nuevo.user = request.user
            nuevo.save()

            # Si venía de postulación, volver a convocatorias IDEA
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect("panel_usuario")  # si entra desde su panel
    else:
        form = PersonaHumanaForm(instance=perfil)

    return render(request, "registro_audiovisual/editar_persona_humana.html", {"form": form})



@login_required
def editar_persona_juridica(request):
    instancia, creado = PersonaJuridica.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = PersonaJuridicaForm(request.POST, instance=instancia)
        if form.is_valid():
            form.save()
            return redirect("panel_usuario")
    else:
        form = PersonaJuridicaForm(instance=instancia)

    return render(request, "registro_audiovisual/editar_persona_juridica.html", {"form": form})


