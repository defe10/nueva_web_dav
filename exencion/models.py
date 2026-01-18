# exencion/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError

from convocatorias.models import Convocatoria
from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .utils import generar_pdf_exencion
import uuid



# ============================================================
# VALIDADORES (PDF + 5MB)
# ============================================================
def validar_pdf(archivo):
    nombre = (archivo.name or "").lower()
    if not nombre.endswith(".pdf"):
        raise ValidationError("Solo se permiten archivos PDF.")


def validar_tamano_5mb(archivo):
    if archivo.size > 5 * 1024 * 1024:
        raise ValidationError("El archivo no puede superar los 5 MB.")


# ============================================================
# EXENCIÓN
# ============================================================
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


# ============================================================
# OBSERVACIONES ADMIN (EXENCIÓN)
# ============================================================
class ObservacionAdministrativaExencion(models.Model):
    TIPOS_DOCUMENTO = [
        ("GENERAL", "Documentación general"),
        ("FISCAL", "Documentación fiscal"),
        ("IDENTIDAD", "Identidad / Personería"),
        ("OTRO", "Otro"),
    ]

    exencion = models.ForeignKey(
        Exencion,
        on_delete=models.CASCADE,
        related_name="observaciones"
    )

    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPOS_DOCUMENTO,
        default="GENERAL",
        help_text="Tipo de documentación a subsanar"
    )

    descripcion = models.CharField(
        max_length=255,
        help_text="Ej: Falta constancia DGR, CUIT ilegible, Acta sin firma, etc."
    )

    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    subsanada = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Observación administrativa (Exención)"
        verbose_name_plural = "Observaciones administrativas (Exención)"

    def __str__(self):
        estado = "OK" if self.subsanada else "Pendiente"
        return f"Exención {self.exencion_id} · {self.get_tipo_documento_display()} · {estado}"


# ============================================================
# DOCUMENTOS (EXENCIÓN)
# ============================================================
class ExencionDocumento(models.Model):
    """
    Documentos asociados a una Exención.
    - Permite múltiples cargas.
    - Permite borrado mientras estén pendientes.
    - Permite "enviar" (confirmar) lote de documentos.
    - Permite distinguir subsanación (cuando el admin observa).
    """

    ESTADOS = [
        ("PENDIENTE", "Pendiente de envío"),
        ("ENVIADO", "Enviado"),
    ]

    exencion = models.ForeignKey(
        Exencion,
        on_delete=models.CASCADE,
        related_name="documentos"
    )

    archivo = models.FileField(
        upload_to="exencion/documentos/",
        validators=[validar_pdf, validar_tamano_5mb],
    )

    fecha_subida = models.DateTimeField(auto_now_add=True)

    # identifica si el documento fue subido como subsanación
    es_subsanacion = models.BooleanField(default=False)

    # estado borrador/enviado (para poder eliminar antes de confirmar)
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="PENDIENTE",
        db_index=True,
    )

    # fecha real de confirmación/envío
    fecha_envio = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha_subida"]
        verbose_name = "Documento de exención"
        verbose_name_plural = "Documentos de exención"

    def __str__(self):
        suf = " (subsanación)" if self.es_subsanacion else ""
        return f"Documento {self.id} – Exención {self.exencion_id}{suf}"


class PadronPublicoExencion(models.Model):
    """
    Habilita un padrón público (no listado) para verificación por QR.
    Si se filtra el link, podés rotar el token creando otro y desactivando este.
    """
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Padrón público de exención"
        verbose_name_plural = "Padrón público de exención"

    def __str__(self):
        estado = "activo" if self.activo else "inactivo"
        return f"Padrón público ({estado}) · {self.token}"