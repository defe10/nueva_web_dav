# sitio_publico/views.py
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from convocatorias.models import Convocatoria
from formacion.models import ConvocatoriaFormacion


def inicio(request):
    hoy = timezone.now().date()
    categoria = request.GET.get("categoria")

    vigentes = list(
        Convocatoria.objects.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy,
        )
    )
    for c in vigentes:
        c.detalle_url = reverse("convocatorias:convocatoria_detalle", args=[c.slug])
        c.categoria_display = c.get_categoria_display()

    # las convocatorias de formación viven en otro modelo:
    # se listan como "Curso / Capacitación"
    formaciones = list(
        ConvocatoriaFormacion.objects.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy,
        )
    )
    for f in formaciones:
        f.detalle_url = reverse("formacion:detalle", args=[f.slug])
        f.categoria = "CURSO"
        f.categoria_display = "Curso / Capacitación"

    todas = vigentes + formaciones
    if categoria:
        todas = [c for c in todas if c.categoria == categoria]

    todas.sort(key=lambda c: (c.orden, -c.fecha_inicio.toordinal()))

    return render(request, "sitio_publico/inicio.html", {"vigentes": todas})


def institucional(request):
    return render(request, "sitio_publico/institucional.html")

def programas(request):
    return render(request, "sitio_publico/programas.html")