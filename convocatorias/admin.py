from django.contrib import admin
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

import io
import os
import zipfile

from registro_audiovisual.models import PersonaHumana, PersonaJuridica

from .models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
    ObservacionAdministrativa,
    AsignacionJuradoConvocatoria,
    InscripcionFormacion,
    Rendicion,  # ✅ NUEVO
)


# ============================================================
#  CONVOCATORIAS
# ============================================================
@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):

    list_display = (
        "titulo",
        "categoria",
        "linea",
        "fecha_inicio",
        "fecha_fin",
        "vigente",
        "orden",
        "url_destino_admin",
    )

    list_filter = (
        "categoria",
        "linea",
        "fecha_inicio",
        "fecha_fin",
    )

    search_fields = (
        "titulo",
        "descripcion_corta",
        "descripcion_larga",
    )

    prepopulated_fields = {"slug": ("titulo",)}
    ordering = ("orden", "-fecha_inicio")

    def url_destino_admin(self, obj):
        if not obj.url_destino:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">abrir</a>',
            obj.url_destino
        )
    url_destino_admin.short_description = "URL destino"


# ============================================================
#  DOCUMENTOS DE LA POSTULACIÓN (INLINE)
# ============================================================
class PostulacionDocumentoInline(admin.TabularInline):
    model = DocumentoPostulacion
    extra = 0
    can_delete = False

    fields = ("tipo", "subtipo_subsanado", "estado", "archivo", "fecha_subida")
    readonly_fields = ("archivo", "fecha_subida")

    def get_formset(self, request, obj=None, **kwargs):
        """
        Evita confusiones:
        - Si NO es SUBSANADO, ocultamos subtipo (o lo dejamos editable pero sin sentido).
        Como TabularInline no permite ocultar por fila fácilmente,
        lo controlamos por validación en el admin (save_model).
        """
        return super().get_formset(request, obj, **kwargs)



# ============================================================
#  POSTULACIONES
# ============================================================
@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):

    # -------------------------
    # LISTADO
    # -------------------------
    list_display = (
        "id_admin",
        "fecha_envio",
        "presentante",
        "nombre_proyecto",
        "convocatoria",
        "linea_convocatoria",
        "estado",
        
    )

    list_filter = (
        "estado",
        "tipo_proyecto",
        "genero",
        "convocatoria",
        "convocatoria__linea",
        "convocatoria__categoria",
    )

    search_fields = (
        "nombre_proyecto",
        "user__username",
        "user__email",
        "convocatoria__titulo",
    )

    ordering = ("-fecha_envio",)

    actions = [
        "descargar_documentacion_zip",
        "exportar_excel_postulaciones",
        "crear_rendicion_para_seleccionados",   # ✅ NUEVO
        "marcar_seleccionado_y_crear_rendicion" # ✅ NUEVO
    ]

    # -------------------------
    # DETALLE (base)
    # -------------------------
    readonly_fields = (
        "presentante",
        "convocatoria",
        "fecha_envio",
        "edad",
        "genero_persona",
        "lugar_residencia",
    )

    inlines = [PostulacionDocumentoInline]

    # ==================================================
    # FIELDSETS DINÁMICOS (línea libre: oculta “Datos del proyecto”)
    # ==================================================
    def get_fieldsets(self, request, obj=None):
        base = (
            ("Datos del presentante", {
                "fields": (
                    "presentante",
                    "fecha_envio",
                    "edad",
                    "genero_persona",
                    "lugar_residencia",
                    "convocatoria",
                )
            }),
        )

        # Creación (obj=None): mostramos todo
        if obj is None:
            return base + (
                ("Datos del proyecto", {
                    "fields": (
                        "nombre_proyecto",
                        "tipo_proyecto",
                        "genero",
                        "estado",
                    )
                }),
            )

        # Edición: si es línea libre, ocultamos datos del proyecto
        if obj.convocatoria and obj.convocatoria.linea == "libre":
            return base + (
                ("Estado", {
                    "fields": ("estado",),
                    "description": "Línea libre: no requiere datos del proyecto. Se gestiona por documentación."
                }),
            )

        # Normal
        return base + (
            ("Datos del proyecto", {
                "fields": (
                    "nombre_proyecto",
                    "tipo_proyecto",
                    "genero",
                    "estado",
                )
            }),
        )

    # ==================================================
    # READONLY EXTRA (línea libre: bloquea campos del proyecto)
    # ==================================================
    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.convocatoria and obj.convocatoria.linea == "libre":
            ro.extend(["nombre_proyecto", "tipo_proyecto", "genero"])
        return ro

    # ==================================================
    # HELPERS PERSONA
    # ==================================================
    def _persona_humana(self, user):
        return PersonaHumana.objects.filter(user=user).first()

    def _persona_juridica(self, user):
        return PersonaJuridica.objects.filter(user=user).first()

    # ==================================================
    # CAMPOS CALCULADOS
    # ==================================================
    def usuario(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user_id)
    usuario.short_description = "ID"

    def id_admin(self, obj):
        url = reverse("admin:convocatorias_postulacion_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.id)

    id_admin.short_description = "ID"
    id_admin.admin_order_field = "id"



    def linea_convocatoria(self, obj):
        return obj.convocatoria.linea if obj.convocatoria else "—"
    linea_convocatoria.short_description = "Línea"

    def presentante(self, obj):
        ph = self._persona_humana(obj.user)
        pj = self._persona_juridica(obj.user)

        if ph:
            url = reverse("admin:registro_audiovisual_personahumana_change", args=[ph.id])
            return format_html('<a href="{}">{}</a>', url, ph.nombre_completo)

        if pj:
            url = reverse("admin:registro_audiovisual_personajuridica_change", args=[pj.id])
            return format_html('<a href="{}">{}</a>', url, pj.razon_social)

        return "—"
    presentante.short_description = "Presentante"

    def edad(self, obj):
        ph = self._persona_humana(obj.user)
        pj = self._persona_juridica(obj.user)
        if ph and getattr(ph, "edad", None) is not None:
            return ph.edad
        if pj and getattr(pj, "antiguedad", None) is not None:
            return pj.antiguedad
        return "—"
    edad.short_description = "Edad"

    def genero_persona(self, obj):
        ph = self._persona_humana(obj.user)
        if ph and getattr(ph, "genero", None):
            try:
                return ph.get_genero_display()
            except Exception:
                return ph.genero
        return "—"
    genero_persona.short_description = "Género"

    def lugar_residencia(self, obj):
        ph = self._persona_humana(obj.user)
        pj = self._persona_juridica(obj.user)

        if ph:
            try:
                return ph.otro_lugar_residencia if ph.lugar_residencia == "otro" else ph.get_lugar_residencia_display()
            except Exception:
                return "—"

        if pj:
            try:
                return pj.otro_lugar_residencia if pj.lugar_residencia == "otro" else pj.get_lugar_residencia_display()
            except Exception:
                return "—"

        return "—"
    lugar_residencia.short_description = "Lugar de residencia"

    # ==================================================
    # ✅ ACCIONES RENDICIÓN
    # ==================================================
    def crear_rendicion_para_seleccionados(self, request, queryset):
        """
        Crea Rendición SOLO para postulaciones ya 'seleccionado'.
        No modifica el estado de la postulación.
        """
        creadas = 0
        ya_existian = 0
        omitidas = 0

        # optimiza accesos
        queryset = queryset.select_related("user", "convocatoria")

        for p in queryset:
            if p.estado != "seleccionado":
                omitidas += 1
                continue

            rendicion, created = Rendicion.objects.get_or_create(
                postulacion=p,
                defaults={"user": p.user},
            )

            # si existía pero el user no coincide (raro), lo alineamos
            if not created and rendicion.user_id != p.user_id:
                rendicion.user = p.user

            # evento
            try:
                if created:
                    rendicion.add_event("admin", "RENDICION_CREADA", f"Creada desde admin para Postulación {p.id}")
                else:
                    rendicion.add_event("admin", "RENDICION_EXISTENTE", f"Ya existía (admin) para Postulación {p.id}")
                rendicion.save()
            except Exception:
                # si algo raro pasa con JSONField no rompemos la acción
                rendicion.save()

            if created:
                creadas += 1
            else:
                ya_existian += 1

        if creadas:
            messages.success(request, f"✅ Rendiciones creadas: {creadas}.")
        if ya_existian:
            messages.info(request, f"ℹ️ Rendiciones ya existentes: {ya_existian}.")
        if omitidas:
            messages.warning(request, f"⚠️ Omitidas (no estaban en estado 'seleccionado'): {omitidas}.")

    crear_rendicion_para_seleccionados.short_description = "📌 Crear Rendición para SELECCIONADOS"

    def marcar_seleccionado_y_crear_rendicion(self, request, queryset):
        """
        Marca postulaciones como 'seleccionado' y crea Rendición.
        Útil cuando ya está decidida la selección y querés habilitar rendición de una.
        """
        actualizadas = 0
        creadas = 0

        queryset = queryset.select_related("user", "convocatoria")

        for p in queryset:
            # setea seleccionado si no lo estaba
            if p.estado != "seleccionado":
                p.estado = "seleccionado"
                p.save(update_fields=["estado"])
                actualizadas += 1

            rendicion, created = Rendicion.objects.get_or_create(
                postulacion=p,
                defaults={"user": p.user},
            )
            if not created and rendicion.user_id != p.user_id:
                rendicion.user = p.user

            try:
                rendicion.add_event("admin", "SELECCIONADO_Y_RENDICION", f"Postulación {p.id} marcada seleccionado y rendición habilitada")
                rendicion.save()
            except Exception:
                rendicion.save()

            if created:
                creadas += 1

        messages.success(
            request,
            f"✅ Postulaciones marcadas como 'seleccionado': {actualizadas}. Rendiciones creadas: {creadas}."
        )

    marcar_seleccionado_y_crear_rendicion.short_description = "🏆 Marcar como SELECCIONADO + crear Rendición"

    # ==================================================
    # ACCIÓN ZIP
    # ==================================================
    def descargar_documentacion_zip(self, request, queryset):
        if queryset.count() == 1:
            return self._zip_para_una_postulacion(queryset.first())

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in queryset:
                zip_bytes, zip_name = self._bytes_zip_para_una_postulacion(p)
                zf.writestr(zip_name, zip_bytes.getvalue())

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="documentacion_postulaciones.zip"'
        return response

    descargar_documentacion_zip.short_description = "📦 Descargar documentación (ZIP)"

    def _agregar_archivo_zip(self, zf, file_field, carpeta, nombre):
        if not file_field:
            return
        try:
            path = getattr(file_field, "path", None)
            if path and os.path.exists(path):
                zf.write(path, f"{carpeta}/{nombre}{os.path.splitext(path)[1]}")
            else:
                with file_field.open("rb") as f:
                    zf.writestr(
                        f"{carpeta}/{nombre}{os.path.splitext(file_field.name)[1]}",
                        f.read()
                    )
        except Exception:
            pass

    def _safe_slug(self, p):
        base = p.nombre_proyecto or f"postulacion_{p.id}"
        return slugify(base)[:40] or f"postulacion_{p.id}"

    def _bytes_zip_para_una_postulacion(self, p):
        buffer = io.BytesIO()
        name = f"postulacion_{p.id}_{self._safe_slug(p)}.zip"
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            self._armar_zip(zf, p)
        buffer.seek(0)
        return buffer, name

    def _zip_para_una_postulacion(self, p):
        buffer = io.BytesIO()
        name = f"postulacion_{p.id}_{self._safe_slug(p)}.zip"
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            self._armar_zip(zf, p)
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{name}"'
        return response

    def _armar_zip(self, zf, p):
        zf.writestr(
            "README.txt",
            f"Postulación ID: {p.id}\n"
            f"Proyecto: {p.nombre_proyecto or '(Sin título)'}\n"
            f"Usuario: {p.user.username}\n"
            f"Convocatoria: {p.convocatoria.titulo if p.convocatoria else ''}\n"
        )
        for doc in p.documentos.all():
            self._agregar_archivo_zip(
                zf,
                doc.archivo,
                "documentacion",
                slugify(doc.get_tipo_display())
            )

    # ==================================================
    # EXPORTAR EXCEL
    # ==================================================
    def exportar_excel_postulaciones(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Postulaciones"

        headers = [
            "Fecha postulación",
            "Usuario",
            "Presentante",
            "Edad",
            "Género (persona)",
            "Lugar de residencia",
            "Convocatoria",
            "Línea",
            "Nombre del proyecto",
            "Tipo de proyecto",
            "Género (proyecto)",
            "Estado",
        ]
        ws.append(headers)

        queryset = queryset.select_related("user", "convocatoria")

        for p in queryset:
            ws.append([
                p.fecha_envio.strftime("%d/%m/%Y %H:%M") if p.fecha_envio else "",
                p.user.username,
                self._presentante_texto(p.user),
                self._edad_texto(p.user),
                self._genero_persona_texto(p.user),
                self._lugar_residencia_texto(p.user),
                p.convocatoria.titulo if p.convocatoria else "",
                p.convocatoria.linea if p.convocatoria else "",
                p.nombre_proyecto or "",
                p.get_tipo_proyecto_display() if p.tipo_proyecto else "",
                p.get_genero_display() if p.genero else "",
                p.get_estado_display() if p.estado else "",
            ])

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 25

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="postulaciones.xlsx"'
        wb.save(response)
        return response

    exportar_excel_postulaciones.short_description = "📤 Exportar seleccionadas a Excel (.xlsx)"

    def _presentante_texto(self, user):
        ph = self._persona_humana(user)
        pj = self._persona_juridica(user)
        if ph:
            return ph.nombre_completo
        if pj:
            return pj.razon_social
        return ""

    def _edad_texto(self, user):
        ph = self._persona_humana(user)
        pj = self._persona_juridica(user)
        if ph and getattr(ph, "edad", None) is not None:
            return ph.edad
        if pj and getattr(pj, "antiguedad", None) is not None:
            return pj.antiguedad
        return ""

    def _genero_persona_texto(self, user):
        ph = self._persona_humana(user)
        if ph and getattr(ph, "genero", None):
            try:
                return ph.get_genero_display()
            except Exception:
                return ph.genero
        return ""

    def _lugar_residencia_texto(self, user):
        ph = self._persona_humana(user)
        pj = self._persona_juridica(user)
        if ph:
            try:
                return ph.otro_lugar_residencia if ph.lugar_residencia == "otro" else ph.get_lugar_residencia_display()
            except Exception:
                return ""
        if pj:
            try:
                return pj.otro_lugar_residencia if pj.lugar_residencia == "otro" else pj.get_lugar_residencia_display()
            except Exception:
                return ""
        return ""


# ============================================================
# INSCRIPCIONES DE FORMACIÓN
# ============================================================
def marcar_admitido(modeladmin, request, queryset):
    queryset.update(estado="admitido")
marcar_admitido.short_description = "✅ Marcar como ADMITIDO"


def marcar_no_admitido(modeladmin, request, queryset):
    queryset.update(estado="no_admitido")
marcar_no_admitido.short_description = "❌ Marcar como NO ADMITIDO"


def marcar_lista_espera(modeladmin, request, queryset):
    queryset.update(estado="lista_espera")
marcar_lista_espera.short_description = "🕒 Marcar como LISTA DE ESPERA"


@admin.register(InscripcionFormacion)
class InscripcionFormacionAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "convocatoria",
        "estado",
        "contacto_email",
        "contacto_telefono",
        "vinculo_sector",
        "fecha",
    )
    list_filter = ("estado", "vinculo_sector", "convocatoria")
    search_fields = ("user__username", "user__email", "nombre", "apellido", "dni", "email", "telefono")
    ordering = ("-fecha",)
    actions = [marcar_admitido, marcar_no_admitido, marcar_lista_espera, "exportar_excel_inscripciones_formacion"]

    readonly_fields = ("user", "convocatoria", "fecha")

    fieldsets = (
        ("Datos del sistema", {"fields": ("user", "convocatoria", "estado", "fecha")}),
        ("Vinculación (si existe Registro Audiovisual)", {"fields": ("persona_humana", "persona_juridica")}),
        ("Datos de contacto (si NO hay registro)", {"fields": ("nombre", "apellido", "dni", "email", "telefono", "localidad")}),
        ("Perfil", {"fields": ("vinculo_sector", "declaracion_jurada")}),
    )

    def usuario(self, obj):
        return obj.user.username
    usuario.short_description = "Usuario"

    def contacto_email(self, obj):
        return obj.user.email or obj.email or "—"
    contacto_email.short_description = "Email"

    def contacto_telefono(self, obj):
        if obj.persona_humana_id and getattr(obj.persona_humana, "telefono", None):
            return obj.persona_humana.telefono
        if obj.persona_juridica_id and getattr(obj.persona_juridica, "telefono", None):
            return obj.persona_juridica.telefono
        return obj.telefono or "—"
    contacto_telefono.short_description = "Teléfono"

    def exportar_excel_inscripciones_formacion(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Formación"

        headers = [
            "Fecha",
            "Usuario",
            "Convocatoria",
            "Estado",
            "Email",
            "Teléfono",
            "Vínculo con el sector",
            "Nombre",
            "Apellido",
            "DNI",
            "Localidad",
            "Tiene Registro Audiovisual",
        ]
        ws.append(headers)

        queryset = queryset.select_related("user", "convocatoria", "persona_humana", "persona_juridica")

        for ins in queryset:
            tiene_registro = bool(ins.persona_humana_id or ins.persona_juridica_id)
            ws.append([
                ins.fecha.strftime("%d/%m/%Y %H:%M") if ins.fecha else "",
                ins.user.username,
                ins.convocatoria.titulo if ins.convocatoria else "",
                ins.get_estado_display() if ins.estado else "",
                ins.user.email or ins.email or "",
                self.contacto_telefono(ins),
                ins.get_vinculo_sector_display() if ins.vinculo_sector else "",
                ins.nombre or "",
                ins.apellido or "",
                ins.dni or "",
                getattr(ins, "get_localidad_display", lambda: ins.localidad)() if ins.localidad else "",
                "SI" if tiene_registro else "NO",
            ])

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 25

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="inscripciones_formacion.xlsx"'
        wb.save(response)
        return response

    exportar_excel_inscripciones_formacion.short_description = "📤 Exportar seleccionadas a Excel (.xlsx)"


# ============================================================
# OBSERVACIONES ADMINISTRATIVAS
# ============================================================
@admin.register(ObservacionAdministrativa)
class ObservacionAdministrativaAdmin(admin.ModelAdmin):
    list_display = (
        "postulacion",
        "tipo_documento",
        "descripcion",
        "subsanada",
        "fecha_creacion",
    )
    list_filter = ("subsanada", "tipo_documento")
    search_fields = ("descripcion",)

    def save_model(self, request, obj, form, change):
        """
        Envía email cuando:
        - Se crea una observación pendiente (subsanada=False), o
        - Se edita y sigue pendiente, y cambió algo relevante (tipo/descripcion/subsanada)
        """
        es_nueva = obj.pk is None

        anterior = None
        if not es_nueva:
            anterior = ObservacionAdministrativa.objects.filter(pk=obj.pk).first()

        super().save_model(request, obj, form, change)

        # Solo avisamos si está pendiente
        if obj.subsanada:
            return

        # Si es edición: solo mandar si cambió algo relevante
        if anterior and (
            anterior.subsanada == obj.subsanada
            and anterior.tipo_documento == obj.tipo_documento
            and (anterior.descripcion or "").strip() == (obj.descripcion or "").strip()
        ):
            return

        postulacion = obj.postulacion
        user = getattr(postulacion, "user", None)
        if not user:
            return

        destinatario = user.email
        if not destinatario:
            messages.warning(request, "No se envió email: el usuario no tiene email cargado.")
            return

        convocatoria_titulo = ""
        if getattr(postulacion, "convocatoria", None):
            convocatoria_titulo = postulacion.convocatoria.titulo or ""

        # ==================================================
        # Link al panel (con fallback para que SIEMPRE exista)
        # Ajustá el último fallback si tu ruta no es /convocatorias/
        # ==================================================
        panel_url = None

        # Panel real
        try:
            panel_url = request.build_absolute_uri(reverse("usuarios:panel_usuario"))
        except Exception:
            panel_url = None

        # Fallback razonable: home de convocatorias (si existe)
        if not panel_url:
            try:
                panel_url = request.build_absolute_uri(reverse("convocatorias:convocatorias_home"))
            except Exception:
                panel_url = None

        # Último fallback (hardcodeado) — con barra final
        if not panel_url:
            panel_url = request.build_absolute_uri("/usuarios/panel/")

        asunto = "Subsanación de documentación requerida"

        contexto = {
            "user": user,
            "postulacion": postulacion,
            "convocatoria_titulo": convocatoria_titulo,
            "observacion": obj,
            "panel_url": panel_url,
            "anio": timezone.now().year,
        }

        texto = (
            "Tenés una subsanación de documentación pendiente.\n\n"
            f"Convocatoria: {convocatoria_titulo or '—'}\n"
            f"Documento: {getattr(obj, 'get_tipo_documento_display', lambda: obj.tipo_documento)()}\n"
            f"Detalle: {obj.descripcion}\n\n"
            + (f"Ingresá al panel para subsanar: {panel_url}\n" if panel_url else "")
        )

        try:
            try:
                html = render_to_string(
                    "convocatorias/subsanacion_documentacion_email.html",
                    contexto
                )
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

            messages.success(request, f"Email de subsanación enviado a {destinatario}.")
        except Exception as e:
            messages.error(request, f"No se pudo enviar el email de subsanación: {e}")


# ============================================================
# ASIGNACIÓN JURADO ⇄ CONVOCATORIA
# ============================================================
@admin.register(AsignacionJuradoConvocatoria)
class AsignacionJuradoConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ("jurado", "convocatoria", "fecha_asignacion")
    list_filter = ("convocatoria",)
    search_fields = ("jurado__username", "convocatoria__titulo")


# ============================================================
# RENDICIÓN
# ============================================================
@admin.register(Rendicion)
class RendicionAdmin(admin.ModelAdmin):
    pass


@admin.register(DocumentoPostulacion)
class DocumentoPostulacionAdmin(admin.ModelAdmin):
    list_display = (
        "postulacion",
        "tipo",
        "subtipo_subsanado",
        "estado",
        "fecha_subida",
    )
    list_filter = ("tipo", "subtipo_subsanado", "estado")
    search_fields = (
        "postulacion__id",
        "postulacion__nombre_proyecto",
        "postulacion__user__username",
        "postulacion__user__email",
    )
    ordering = ("-fecha_subida",)

    def save_model(self, request, obj, form, change):
        # Si no es SUBSANADO, el subtipo no debe quedar seteado
        if obj.tipo != "SUBSANADO":
            obj.subtipo_subsanado = None

        # Si es SUBSANADO, forzamos que tenga subtipo (para que jurado vea lo correcto)
        if obj.tipo == "SUBSANADO" and not obj.subtipo_subsanado:
            messages.error(
                request,
                "⚠️ Si el tipo es SUBSANADO, debés seleccionar Subtipo (PROYECTO o ADMIN)."
            )
            return  # corta el guardado

        super().save_model(request, obj, form, change)

