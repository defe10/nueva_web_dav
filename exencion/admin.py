from django.contrib import admin, messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import Exencion, ExencionDocumento, ObservacionAdministrativaExencion


# ============================================================
# ADMIN EXENCIÓN
# ============================================================
@admin.register(Exencion)
class ExencionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "fecha_creacion",
        "estado",
        "presentante",          # ✅ clickable (en vez de nombre_razon_social)
        "cuit",
        "email",
        "convocatoria",
    )

    list_filter = ("estado", "fecha_creacion")
    search_fields = ("nombre_razon_social", "cuit", "email")

    actions = ["aprobar_exencion_y_emitir_pdf"]

    # OJO: NO hay inlines -> no aparece “Documentos de exención”
    # inlines = [...]

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_emision",
        "fecha_vencimiento",
        "certificado_pdf",

        # ✅ presentante como en Postulación
        "presentante",

        # Datos congelados / visibles
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

        "documentacion_resumen",
    )

    fieldsets = (
        ("Datos del trámite", {
            "fields": (
                "id",
                "fecha_creacion",
                "estado",
                "convocatoria",
                "certificado_pdf",
                "fecha_emision",
                "fecha_vencimiento",
            )
        }),
        ("Datos del solicitante", {
            "fields": (
                "presentante",       # ✅ clickable
                "nombre_razon_social",
                "cuit",
                "email",
                "persona_humana",
                "persona_juridica",
            )
        }),
        ("Datos fiscales (congelados)", {
            "fields": (
                "domicilio_fiscal",
                "localidad_fiscal",
                "codigo_postal_fiscal",
                "actividad_dgr",
            )
        }),
        ("Documentación adjunta", {
            "fields": ("documentacion_resumen",),
            "description": "Se muestra acá para control interno. No existe el modelo 'Documentos de exención' en el menú."
        }),
    )

    # -------------------------------------------------
    # PRESENTANTE (LINK AL REGISTRO) ✅
    # -------------------------------------------------
    def presentante(self, obj):
        """
        Muestra el Nombre/Razón social como link al 'registro' (admin change)
        de PersonaHumana o PersonaJuridica, como tu presentante en Postulación.
        """
        ph = getattr(obj, "persona_humana", None)
        pj = getattr(obj, "persona_juridica", None)

        # Texto visible (lo que se cliquea)
        label = (getattr(obj, "nombre_razon_social", "") or "—").strip()

        # Si no hay registro asociado, devolvemos solo texto
        if not ph and not pj:
            return label

        # Elegimos a cuál linkear
        target = ph or pj

        url = reverse(
            f"admin:{target._meta.app_label}_{target._meta.model_name}_change",
            args=[target.pk],
        )

        # Si querés agregar ID en el texto:
        # return format_html('<a href="{}">{} (ID {})</a>', url, label, target.pk)

        return format_html('<a href="{}">{}</a>', url, label)

    presentante.short_description = "Presentante"
    presentante.admin_order_field = "nombre_razon_social"

    # -------------------------------------------------
    # RESUMEN DE DOCUMENTACIÓN (HTML REAL, no texto)
    # -------------------------------------------------
    def documentacion_resumen(self, obj):
        docs = obj.documentos.all().order_by("-fecha_subida")
        if not docs.exists():
            return "—"

        filas = []

        for d in docs:
            # Badge ORIGINAL / SUBSANADO
            if d.es_subsanacion:
                badge = format_html(
                    '<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
                    'font-size:12px;line-height:18px;background:#fff3cd;color:#856404;'
                    'border:1px solid #ffeeba;">SUBSANADO</span>'
                )
            else:
                badge = format_html(
                    '<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
                    'font-size:12px;line-height:18px;background:#e7f1ff;color:#084298;'
                    'border:1px solid #b6d4fe;">ORIGINAL</span>'
                )

            # Nombre del archivo
            nombre_archivo = d.archivo.name.split("/")[-1] if d.archivo else "—"

            # Link al archivo
            link = (
                format_html(
                    '<a href="{}" target="_blank" rel="noopener">{}</a>',
                    d.archivo.url,
                    nombre_archivo,
                )
                if d.archivo else nombre_archivo
            )

            fecha = d.fecha_subida.strftime("%d/%m/%Y %H:%M") if d.fecha_subida else "—"

            filas.append((badge, link, fecha))

        return format_html_join(
            "<br>",
            "{} {} · {}",
            filas
        )

    documentacion_resumen.short_description = "Documentación"

    # -------------------------------------------------
    # ACCIÓN ADMINISTRATIVA
    # -------------------------------------------------
    @admin.action(description="Aprobar exención y emitir constancia PDF")
    def aprobar_exencion_y_emitir_pdf(self, request, queryset):

        procesadas = 0
        saltadas = 0

        for exencion in queryset:

            if exencion.estado != "ENVIADA":
                saltadas += 1
                continue

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

            try:
                exencion.aprobar_y_generar_pdf()
                self.message_user(
                    request,
                    f"OK Exención #{exencion.id}: PDF generado y (si correspondía) email enviado.",
                    level=messages.SUCCESS
                )
                procesadas += 1

            except Exception as e:
                self.message_user(
                    request,
                    f"ERROR al generar/enviar Exención #{exencion.id}: {type(e).__name__} - {e}",
                    level=messages.ERROR
                )

        self.message_user(
            request,
            f"{procesadas} exención/es aprobada/s y procesadas. {saltadas} saltada/s (no estaban ENVIADAS).",
            level=messages.SUCCESS
        )



# ============================================================
# OBSERVACIONES ADMINISTRATIVAS (EXENCIÓN) + EMAIL
# ============================================================
@admin.register(ObservacionAdministrativaExencion)
class ObservacionAdministrativaExencionAdmin(admin.ModelAdmin):

    list_display = (
        "exencion",
        "tipo_documento",
        "descripcion",
        "subsanada",
        "fecha_creacion",
    )

    list_filter = ("subsanada", "tipo_documento")
    search_fields = ("descripcion", "exencion__nombre_razon_social", "exencion__cuit", "exencion__email")

    def save_model(self, request, obj, form, change):
        es_nueva = obj.pk is None

        anterior = None
        if not es_nueva:
            anterior = ObservacionAdministrativaExencion.objects.filter(pk=obj.pk).first()

        super().save_model(request, obj, form, change)

        if obj.subsanada:
            return

        if anterior and (
            anterior.subsanada == obj.subsanada
            and anterior.tipo_documento == obj.tipo_documento
            and (anterior.descripcion or "").strip() == (obj.descripcion or "").strip()
        ):
            return

        exencion = obj.exencion
        user = getattr(exencion, "user", None)
        if not user:
            return

        destinatario = exencion.email or getattr(user, "email", "")
        if not destinatario:
            messages.warning(request, "No se envió email: la exención no tiene email y el usuario tampoco.")
            return

        # Links
        panel_url = request.build_absolute_uri(reverse("usuarios:panel_usuario"))
        subsanar_url = request.build_absolute_uri(
            reverse("exencion:subir_documento_subsanado_exencion", args=[exencion.id])
        )

        asunto = "Subsanación de documentación requerida (Exención)"

        contexto = {
            "user": user,
            "exencion": exencion,
            "observacion": obj,
            "panel_url": panel_url,
            "subsanar_url": subsanar_url,
            "anio": timezone.now().year,
        }

        texto = (
            "Tenés una subsanación de documentación pendiente (Exención).\n\n"
            f"Exención: #{exencion.id}\n"
            f"Constancia: {exencion.numero_constancia}\n"
            f"Documento: {getattr(obj, 'get_tipo_documento_display', lambda: obj.tipo_documento)()}\n"
            f"Detalle: {obj.descripcion}\n\n"
            f"Subí la documentación desde acá: {subsanar_url}\n"
            f"También podés entrar al panel: {panel_url}\n"
        )

        try:
            html = None
            try:
                html = render_to_string("exencion/subsanacion_documentacion_email.html", contexto)
            except Exception:
                html = None

            email = EmailMultiAlternatives(
                subject=asunto,
                body=texto,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[destinatario],
            )
            if html:
                email.attach_alternative(html, "text/html")
            email.send(fail_silently=False)

            messages.success(request, f"Email de subsanación (Exención) enviado a {destinatario}.")
        except Exception as e:
            messages.error(request, f"No se pudo enviar el email de subsanación (Exención): {e}")
