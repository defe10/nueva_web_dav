from django.db import models
from django.conf import settings
from django.utils import timezone

from django.core.files.base import ContentFile
from django.core.mail import EmailMessage

from convocatorias.models import Convocatoria
from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .utils import generar_pdf_exencion


ESTADOS_EXENCION = [
    ("ENVIADA", "Enviada"),
    ("APROBADA", "Aprobada"),
    ("RECHAZADA", "Rechazada"),
]


class Exencion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    convocatoria = models.ForeignKey(
        Convocatoria,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Puede venir de una convocatoria o ser independiente"
    )

    # Vínculo con registro audiovisual
    persona_humana = models.ForeignKey(
        PersonaHumana,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    persona_juridica = models.ForeignKey(
        PersonaJuridica,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    # Datos que van al PDF (congelados en la exención)
    nombre_razon_social = models.CharField(max_length=255)
    email = models.EmailField()
    cuit = models.CharField(max_length=20)

    domicilio_fiscal = models.CharField(max_length=255)
    localidad_fiscal = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal_fiscal = models.CharField(max_length=10, blank=True, null=True)

    actividad_dgr = models.CharField(max_length=255)

    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_EXENCION,
        default="ENVIADA"
    )

    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    # PDF generado
    certificado_pdf = models.FileField(
        upload_to="exencion/certificados/",
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Exención impositiva"
        verbose_name_plural = "Exenciones impositivas"

    def __str__(self):
        return f"Exención #{self.id} – {self.nombre_razon_social}"

    @property
    def numero_constancia(self):
        return f"FRC-75-{self.id:05d}"

    def marcar_aprobada(self):
        """
        Marca la exención como aprobada y setea fechas.
        NO genera PDF ni envía mails.
        """
        hoy = timezone.now().date()

        self.estado = "APROBADA"
        self.fecha_emision = hoy
        self.fecha_vencimiento = hoy.replace(year=hoy.year + 1)
        self.save(update_fields=["estado", "fecha_emision", "fecha_vencimiento"])

    def aprobar_y_generar_pdf(self):
        """
        Aprueba la exención, genera el PDF y lo envía por mail.
        (Útil si querés llamarlo desde admin o desde otra capa)
        """
        # 1) Aprobar
        self.marcar_aprobada()

        # 2) Generar PDF
        pdf_content = generar_pdf_exencion(self)
        filename = f"Constancia_{self.numero_constancia}.pdf"

        self.certificado_pdf.save(
            filename,
            ContentFile(pdf_content),
            save=True
        )

        # 3) Enviar correo
        if self.email:
            email = EmailMessage(
                subject=f"Constancia de exención {self.numero_constancia}",
                body=(
                    f"Hola {self.nombre_razon_social},\n\n"
                    "Tu solicitud de exención impositiva fue aprobada.\n"
                    "Adjuntamos la constancia en formato PDF.\n\n"
                    "Secretaría de Cultura de Salta"
                ),
                to=[self.email],
            )
            email.attach(filename, pdf_content, "application/pdf")
            email.send()


class ExencionDocumento(models.Model):
    exencion = models.ForeignKey(
        Exencion,
        on_delete=models.CASCADE,
        related_name="documentos"
    )
    archivo = models.FileField(upload_to="exencion/documentos/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento de exención"
        verbose_name_plural = "Documentos de exención"

    def __str__(self):
        return f"Documento {self.id} – Exención {self.exencion_id}"
