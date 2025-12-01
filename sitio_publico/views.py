# sitio_publico/views.py
from django.shortcuts import render   # 👈 IMPORT CLAVE
from django.utils import timezone
from convocatorias.models import Convocatoria


def inicio(request):
    hoy = timezone.now().date()

    convocatorias_vigentes = Convocatoria.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    )

    return render(request, "sitio_publico/inicio.html", {
        "vigentes": convocatorias_vigentes
    })
