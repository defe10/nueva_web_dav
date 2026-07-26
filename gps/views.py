from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from convocatorias.models import Postulacion
from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from .forms import CreditoFormSet, FichaTecnicaForm, HitoForm, ObraForm
from .models import FichaTecnica, Hito, Obra
from .registro import buscar as buscar_registro


def gps_activo(vista):
    """404 mientras el módulo no esté habilitado (settings.GPS_ACTIVO).

    Deja subir el GPS al servidor sin abrirlo: las pantallas del titular no
    existen ni tipeando la URL, pero el /admin sigue funcionando para el staff.
    Va por fuera de login_required para no delatar el módulo con un redirect
    al login.
    """
    @wraps(vista)
    def envoltorio(request, *args, **kwargs):
        if not getattr(settings, "GPS_ACTIVO", False):
            raise Http404("El registro de obras todavía no está disponible.")
        return vista(request, *args, **kwargs)
    return envoltorio


def _falta_registro(request):
    """Redirección al Registro Audiovisual si el usuario todavía no lo completó.

    Devuelve None si puede seguir. Mismo criterio que exención: la obra vincula
    Dirección/Producción con el registro, así que se exige tenerlo primero. El
    staff queda exento (entra por el /admin, no tiene obras propias).
    """
    if request.user.is_staff:
        return None

    tiene_registro = (
        PersonaHumana.objects.filter(user=request.user).exists()
        or PersonaJuridica.objects.filter(user=request.user).exists()
    )
    if tiene_registro:
        return None

    messages.warning(
        request,
        "Para registrar tus obras primero debés completar tu Registro Audiovisual.",
    )
    return redirect(
        reverse("registro_audiovisual:seleccionar_tipo_registro")
        + f"?next={request.path}"
    )


@gps_activo
@login_required(login_url="/usuarios/login/")
def registro_buscar(request):
    """Autocompletado para vincular Dirección/Producción con el Registro."""
    resultados = buscar_registro(request.GET.get("q", ""))
    return JsonResponse({"resultados": resultados})


# Del tipo de proyecto de la postulación al formato de la obra. Lo que no tiene
# equivalente (TV, publicidad, transmedia, otro) queda sin elegir.
_FORMATO_POR_TIPO = {
    "cine_corto":          "cortometraje",
    "cine_largo":          "largometraje",
    "corto_animacion":     "cortometraje",
    "largo_animacion":     "largometraje",
    "serie":               "serie",
    "serie_web":           "serie",
    "serie_animacion":     "serie",
    "serieweb_animacion":  "serie",
    "videoclip":           "videoclip",
    "videoclip_animacion": "videoclip",
    "videojuego":          "videojuego",
}


def _inicial_desde_postulacion(request):
    """Datos para arrancar la obra a partir de una postulación del usuario.

    Es el camino que ofrece el panel a los proyectos seleccionados: en vez de
    crear la obra sola, se le prellena al titular con lo que ya declaró. Todo
    queda editable, porque el proyecto pudo cambiar desde que se postuló.
    """
    pk = request.GET.get("postulacion")
    if not pk:
        return None

    postulacion = (
        Postulacion.objects
        .filter(pk=pk, user=request.user)
        .select_related("convocatoria")
        .first()
    )
    if postulacion is None:
        return None

    fecha = postulacion.fecha_envio or postulacion.fecha_creacion
    return {
        "titulo": postulacion.nombre_proyecto or "",
        # Las choices de género son las mismas en los dos modelos.
        "genero": postulacion.genero,
        "formato": _FORMATO_POR_TIPO.get(postulacion.tipo_proyecto, ""),
        "sinopsis": postulacion.sinopsis_corta,
        "anio_inicio": fecha.year if fecha else None,
        "postulaciones": [postulacion.pk],
    }


def _obra_del_usuario(request, pk):
    """Obra accesible por el usuario: titular o staff (carga mixta)."""
    obra = get_object_or_404(Obra, pk=pk)
    if obra.owner_id != request.user.id and not request.user.is_staff:
        raise Http404("Obra no encontrada")
    return obra


@gps_activo
@login_required(login_url="/usuarios/login/")
def mis_obras(request):
    """Obras del titular. El listado completo para la Secretaría vive en /admin."""
    redireccion = _falta_registro(request)
    if redireccion:
        return redireccion

    obras = Obra.objects.filter(owner=request.user)
    return render(request, "gps/mis_obras.html", {"obras": obras})


@gps_activo
@login_required(login_url="/usuarios/login/")
def obra_crear(request):
    redireccion = _falta_registro(request)
    if redireccion:
        return redireccion

    if request.method == "POST":
        form = ObraForm(request.POST, user=request.user)
        if form.is_valid():
            # El titular se fija antes de guardar para que el form corra
            # completo (postulaciones y títulos anteriores incluidos).
            form.instance.owner = request.user
            obra = form.save()
            messages.success(request, "Obra creada. Ya podés cargar su trayectoria.")
            return redirect("gps:obra_detalle", pk=obra.pk)
    else:
        form = ObraForm(user=request.user, initial=_inicial_desde_postulacion(request))
    return render(request, "gps/obra_form.html", {"form": form, "obra": None})


@gps_activo
@login_required(login_url="/usuarios/login/")
def obra_editar(request, pk):
    obra = _obra_del_usuario(request, pk)
    if request.method == "POST":
        form = ObraForm(request.POST, instance=obra, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Obra actualizada.")
            return redirect("gps:obra_detalle", pk=obra.pk)
    else:
        form = ObraForm(instance=obra, user=request.user)
    return render(request, "gps/obra_form.html", {"form": form, "obra": obra})


@gps_activo
@login_required(login_url="/usuarios/login/")
def obra_detalle(request, pk):
    obra = _obra_del_usuario(request, pk)
    hitos = obra.hitos.all()  # ordenados por -anio, -fecha (Meta)
    return render(request, "gps/obra_detalle.html", {
        "obra": obra,
        "hitos": hitos,
        "postulaciones": obra.postulaciones.select_related("convocatoria"),
        "titulos_anteriores": obra.titulos_anteriores.all(),
    })


@gps_activo
@login_required(login_url="/usuarios/login/")
def ficha_editar(request, obra_pk):
    obra = _obra_del_usuario(request, obra_pk)
    ficha, _ = FichaTecnica.objects.get_or_create(obra=obra)
    if request.method == "POST":
        form = FichaTecnicaForm(request.POST, instance=ficha)
        creditos = CreditoFormSet(request.POST, instance=ficha, prefix="creditos")
        if form.is_valid() and creditos.is_valid():
            form.save()
            creditos.save()
            messages.success(request, "Ficha técnica guardada.")
            return redirect("gps:obra_detalle", pk=obra.pk)
    else:
        form = FichaTecnicaForm(instance=ficha)
        creditos = CreditoFormSet(instance=ficha, prefix="creditos")
    return render(request, "gps/ficha_form.html", {
        "form": form, "creditos": creditos, "obra": obra,
    })


@gps_activo
@login_required(login_url="/usuarios/login/")
def hito_crear(request, obra_pk):
    obra = _obra_del_usuario(request, obra_pk)
    if request.method == "POST":
        form = HitoForm(request.POST, request.FILES, obra=obra)
        if form.is_valid():
            hito = form.save(commit=False)
            hito.obra = obra
            hito.creado_por = request.user
            hito.save()
            messages.success(request, "Hito agregado a la trayectoria.")
            return redirect("gps:obra_detalle", pk=obra.pk)
    else:
        form = HitoForm(obra=obra)
    return render(request, "gps/hito_form.html", {"form": form, "obra": obra, "hito": None})


@gps_activo
@login_required(login_url="/usuarios/login/")
def hito_editar(request, pk):
    hito = get_object_or_404(Hito, pk=pk)
    obra = _obra_del_usuario(request, hito.obra_id)
    if request.method == "POST":
        form = HitoForm(request.POST, request.FILES, instance=hito, obra=obra)
        if form.is_valid():
            form.save()
            messages.success(request, "Hito actualizado.")
            return redirect("gps:obra_detalle", pk=obra.pk)
    else:
        form = HitoForm(instance=hito, obra=obra)
    return render(request, "gps/hito_form.html", {"form": form, "obra": obra, "hito": hito})


@gps_activo
@login_required(login_url="/usuarios/login/")
def hito_eliminar(request, pk):
    hito = get_object_or_404(Hito, pk=pk)
    obra = _obra_del_usuario(request, hito.obra_id)
    if request.method == "POST":
        hito.delete()
        messages.success(request, "Hito eliminado.")
    return redirect("gps:obra_detalle", pk=obra.pk)
