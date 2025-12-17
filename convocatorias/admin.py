from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from .models import (
    Convocatoria,
    Postulacion,
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
#  POSTULACIONES (IDEA / CASH / FUTURAS)
# ============================================================

@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):

    list_display = (
        "nombre_proyecto",
        "presentante",
        "convocatoria",
        "tipo_proyecto",
        "genero",
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

    actions = ["exportar_excel_postulaciones"]

    readonly_fields = (
        "fecha_envio",
        "presentante",
        "edad",
        "genero_persona",
        "lugar_residencia",
    )

    fieldsets = (
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
        ("Datos del proyecto", {
            "fields": (
                "nombre_proyecto",
                "tipo_proyecto",
                "genero",
                "estado",
            )
        }),
    )

    # --------------------------------------------------
    # DATOS DEL PRESENTANTE
    # --------------------------------------------------
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
            return (
                ph.otro_lugar_residencia
                if ph.lugar_residencia == "otro"
                else ph.get_lugar_residencia_display()
            )
        if pj:
            return (
                pj.otro_lugar_residencia
                if pj.lugar_residencia == "otro"
                else pj.get_lugar_residencia_display()
            )
        return "—"

    lugar_residencia.short_description = "Lugar de residencia"

    # --------------------------------------------------
    # EXPORTAR EXCEL
    # --------------------------------------------------
    def exportar_excel_postulaciones(self, request, queryset):

        wb = Workbook()
        ws = wb.active
        ws.title = "Postulaciones"

        headers = [
            "Fecha postulación",
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
            ph = getattr(p.user, "persona_humana", None)
            pj = getattr(p.user, "persona_juridica", None)

            ws.append([
                p.fecha_envio.strftime("%d/%m/%Y %H:%M"),
                ph.nombre_completo if ph else pj.razon_social if pj else p.user.username,
                ph.edad if ph else pj.antiguedad if pj else "",
                ph.get_genero_display() if ph and ph.genero else "—",
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
