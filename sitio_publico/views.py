# sitio_publico/views.py
from django.shortcuts import render
from django.utils import timezone
from convocatorias.models import Convocatoria


def inicio(request):
    hoy = timezone.now().date()
    categoria = request.GET.get("categoria")

    convocatorias_vigentes = Convocatoria.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    )

    if categoria:
        convocatorias_vigentes = convocatorias_vigentes.filter(
            categoria=categoria
        )

    return render(
        request,
        "sitio_publico/inicio.html",
        {
            "vigentes": convocatorias_vigentes
        }
    )


def institucional(request):
    return render(request, "sitio_publico/institucional.html")

def programas(request):
    return render(request, "sitio_publico/programas.html")