from django.db import models
from django.contrib.auth.models import User
from convocatorias.models import Convocatoria


class ExencionSolicitud(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("APROBADA", "Aprobada"),
            ("RECHAZADA", "Rechazada"),
        ],
        default="PENDIENTE"
    )

    def __str__(self):
        return f"Solicitud #{self.id} – {self.user}"


class ExencionDocumento(models.Model):
    solicitud = models.ForeignKey(ExencionSolicitud, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="exencion/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Documento {self.id} – Solicitud {self.solicitud_id}"
