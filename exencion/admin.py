from django.contrib import admin, messages
from django.utils import timezone

from .models import Exencion, ExencionDocumento


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
        "localidad_fiscal",
        "codigo_postal_fiscal",
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

            # Seguridad: si por algún motivo no tiene datos clave, avisar y saltar
            # (esto no reemplaza tu validación del flujo, pero evita aprobar basura)
            faltan = []
            if not exencion.domicilio_fiscal:
                faltan.append("domicilio_fiscal")
            if not exencion.codigo_postal_fiscal:
                faltan.append("codigo_postal_fiscal")
            if not exencion.localidad_fiscal:
                faltan.append("localidad_fiscal")
            if not exencion.actividad_dgr:
                faltan.append("actividad_dgr")
            if not exencion.cuit:
                faltan.append("cuit")
            if not exencion.nombre_razon_social:
                faltan.append("nombre_razon_social")
            if not exencion.email:
                faltan.append("email")

            if faltan:
                self.message_user(
                    request,
                    f"NO se aprobó Exención #{exencion.id}: faltan datos ({', '.join(faltan)})",
                    level=messages.ERROR
                )
                continue

            # 1) Cambiar estado y fechas (si querés que quede consistente antes del PDF)
            hoy = timezone.now().date()
            exencion.estado = "APROBADA"
            exencion.fecha_emision = hoy
            exencion.fecha_vencimiento = hoy.replace(year=hoy.year + 1)
            exencion.save(update_fields=["estado", "fecha_emision", "fecha_vencimiento"])

            # 2) Generar PDF + guardar + enviar email
            # (usa el método del modelo que ya te dejé en exencion/models.py)
            try:
                exencion.aprobar_y_generar_pdf()

                self.message_user(
                    request,
                    f"OK Exención #{exencion.id}: PDF generado y (si correspondía) email enviado.",
                    level=messages.SUCCESS
                )

            except Exception as e:
                # Si falla, lo dejamos en APROBADA pero sin PDF/email -> vos decidís si querés revertir estado
                self.message_user(
                    request,
                    f"ERROR al generar/enviar Exención #{exencion.id}: {type(e).__name__} - {e}",
                    level=messages.ERROR
                )
                continue

            procesadas += 1

        self.message_user(
            request,
            f"{procesadas} exención/es aprobada/s y procesadas.",
            level=messages.SUCCESS
        )
