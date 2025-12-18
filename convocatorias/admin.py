from django.contrib import admin
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.html import format_html

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

import io
import os
import zipfile

from .models import (
    Convocatoria,
    Postulacion,
    DocumentoPostulacion,
)
from django.urls import path


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


# ============================================================
#  DOCUMENTOS DE LA POSTULACIÓN (INLINE)
# ============================================================

class PostulacionDocumentoInline(admin.TabularInline):
    model = DocumentoPostulacion
    extra = 0
    readonly_fields = ("archivo", "fecha_subida")
    can_delete = False


# ============================================================
#  POSTULACIONES
# ============================================================

@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):

    # -------------------------
    # LISTADO
    # -------------------------
    list_display = (
        "usuario",
        "presentante",
        "nombre_proyecto",
        "convocatoria",
        "estado",
        "fecha_envio",
    )

    list_filter = (
        "estado",
        "tipo_proyecto",
        "genero",
        "convocatoria",
    )

    search_fields = (
        "nombre_proyecto",
        "user__username",
        "user__email",
    )

    ordering = ("-fecha_envio",)

    actions = [
        "descargar_documentacion_zip",
        "exportar_excel_postulaciones",
    ]

    # -------------------------
    # DETALLE
    # -------------------------
    readonly_fields = (
        "user",
        "presentante",
        "convocatoria",
        "fecha_envio",
        "edad",
        "genero_persona",
        "lugar_residencia",
    )

    fieldsets = (
        ("Datos del presentante", {
            "fields": (
                "user",
                "presentante",
                "fecha_envio",
                "edad",
                "genero_persona",
                "lugar_residencia",
                "convocatoria",
            )
        }),
        ("Datos del proyecto", {
            "fields": (
                "nombre_proyecto",
                "tipo_proyecto",
                "genero",
                "estado",
            )
        }),
        
    )

    inlines = [PostulacionDocumentoInline]

    # ==================================================
    # CAMPOS CALCULADOS
    # ==================================================
    def usuario(self, obj):
        return obj.user.username
    usuario.short_description = "Usuario"

    def presentante(self, obj):
        ph = getattr(obj.user, "persona_humana", None)
        pj = getattr(obj.user, "persona_juridica", None)
        if ph:
            return ph.nombre_completo
        if pj:
            return pj.razon_social
        return obj.user.username
    presentante.short_description = "Presentante"

    def edad(self, obj):
        ph = getattr(obj.user, "persona_humana", None)
        pj = getattr(obj.user, "persona_juridica", None)
        if ph:
            return ph.edad
        if pj:
            return pj.antiguedad
        return "—"
    edad.short_description = "Edad"

    def genero_persona(self, obj):
        ph = getattr(obj.user, "persona_humana", None)
        if ph and ph.genero:
            return ph.get_genero_display()
        return "—"
    genero_persona.short_description = "Género"

    def lugar_residencia(self, obj):
        ph = getattr(obj.user, "persona_humana", None)
        pj = getattr(obj.user, "persona_juridica", None)
        if ph:
            return ph.otro_lugar_residencia if ph.lugar_residencia == "otro" else ph.get_lugar_residencia_display()
        if pj:
            return pj.otro_lugar_residencia if pj.lugar_residencia == "otro" else pj.get_lugar_residencia_display()
        return "—"
    lugar_residencia.short_description = "Lugar de residencia"

    # ==================================================
    # BOTÓN ZIP EN EL DETALLE
    # ==================================================
    # ==================================================
    # URLs custom del admin
    # ==================================================
   

    # ==================================================
    # VIEW: descargar ZIP desde el detalle
    # ==================================================
    def descargar_zip_view(self, request, postulacion_id):
        postulacion = self.get_object(request, postulacion_id)
        return self._zip_para_una_postulacion(postulacion)

  




    # ==================================================
    # ACCIÓN ZIP (LISTADO)
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

    # -------------------------
    # HELPERS ZIP
    # -------------------------
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

    def _bytes_zip_para_una_postulacion(self, p):
        buffer = io.BytesIO()
        name = f"postulacion_{p.id}_{slugify(p.nombre_proyecto)[:40]}.zip"
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            self._armar_zip(zf, p)
        buffer.seek(0)
        return buffer, name

    def _zip_para_una_postulacion(self, p):
        buffer = io.BytesIO()
        name = f"postulacion_{p.id}_{slugify(p.nombre_proyecto)[:40]}.zip"
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
            f"Proyecto: {p.nombre_proyecto}\n"
            f"Usuario: {p.user.username}\n"
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
            "Nombre del proyecto",
            "Tipo de proyecto",
            "Género (proyecto)",
        ]
        ws.append(headers)

        queryset = queryset.select_related("user", "convocatoria")

        for p in queryset:
            ws.append([
                p.fecha_envio.strftime("%d/%m/%Y %H:%M"),
                p.user.username,
                self.presentante(p),
                self.edad(p),
                self.genero_persona(p),
                self.lugar_residencia(p),
                p.convocatoria.titulo if p.convocatoria else "",
                p.nombre_proyecto,
                p.get_tipo_proyecto_display(),
                p.get_genero_display(),
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
