from django.contrib import admin, messages
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import Exencion, ExencionDocumento
from .utils import generar_pdf_exencion



# ============================================================
# DOCUMENTOS DE LA EXENCIÓN (INLINE)
# ============================================================
class ExencionDocumentoInline(admin.TabularInline):
    model = ExencionDocumento
    extra = 0
    readonly_fields = ("archivo", "fecha_subida")
    can_delete = False


# ============================================================
# ADMIN EXENCIÓN
# ============================================================
@admin.register(Exencion)
class ExencionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "fecha_creacion",
        "estado",
        "nombre_razon_social",
        "cuit",
        "email",
        "convocatoria",
    )

    list_filter = ("estado", "fecha_creacion")
    search_fields = ("nombre_razon_social", "cuit", "email")

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_emision",
        "fecha_vencimiento",
        "certificado_pdf",
        "nombre_razon_social",
        "cuit",
        "domicilio_fiscal",
        "actividad_dgr",
        "email",
        "persona_humana",
        "persona_juridica",
        "convocatoria",
    )

    inlines = [ExencionDocumentoInline]

    actions = ["aprobar_exencion_y_emitir_pdf"]

    # -------------------------------------------------
    # ACCIÓN ADMINISTRATIVA
    # -------------------------------------------------
    @admin.action(description="Aprobar exención y emitir constancia PDF")
    def aprobar_exencion_y_emitir_pdf(self, request, queryset):

        procesadas = 0

        for exencion in queryset:

            # Solo procesar exenciones ENVIADAS
            if exencion.estado != "ENVIADA":
                continue

            # 1) Cambiar estado y fechas
            hoy = timezone.now().date()
            exencion.estado = "APROBADA"
            exencion.fecha_emision = hoy
            exencion.fecha_vencimiento = hoy.replace(year=hoy.year + 1)
            exencion.save()

            # 2) Generar PDF + guardar en el modelo (con debug)
            try:
                pdf_content = generar_pdf_exencion(exencion)
                if not pdf_content:
                    raise Exception("generar_pdf_exencion devolvió vacío (0 bytes)")

                filename = f"Constancia_{exencion.numero_constancia}.pdf"
                exencion.certificado_pdf.save(
                    filename,
                    ContentFile(pdf_content),
                    save=True
                )

                # debug: confirmar que quedó guardado
                self.message_user(
                    request,
                    f"PDF OK para Exención #{exencion.id}: {exencion.certificado_pdf.name}",
                    level=messages.SUCCESS
                )

            except Exception as e:
                self.message_user(
                    request,
                    f"ERROR PDF Exención #{exencion.id}: {type(e).__name__} - {e}",
                    level=messages.ERROR
                )
                continue

            # 3) Enviar correo (si hay email)
            if exencion.email:
                try:
                    email = EmailMessage(
                        subject=f"Constancia de exención {exencion.numero_constancia}",
                        body=(
                            f"Hola {exencion.nombre_razon_social},\n\n"
                            "Tu solicitud de exención impositiva fue aprobada.\n"
                            "Adjuntamos la constancia correspondiente.\n\n"
                            "Secretaría de Cultura de Salta"
                        ),
                        to=[exencion.email],
                    )
                    email.attach(filename, pdf_content, "application/pdf")
                    email.send(fail_silently=False)

                except Exception as e:
                    self.message_user(
                        request,
                        f"ERROR EMAIL Exención #{exencion.id}: {type(e).__name__} - {e}",
                        level=messages.ERROR
                    )

            procesadas += 1

        self.message_user(
            request,
            f"{procesadas} exención/es aprobada/s y procesadas.",
            level=messages.SUCCESS
        )
