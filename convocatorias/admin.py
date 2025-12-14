from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from .models import (
    Convocatoria,
    PostulacionIDEA,
    DocumentoPersonal,
    DocumentoProyecto,
    InscripcionCurso,
)

# ============================================================
#  CONVOCATORIA
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

    fieldsets = (

        ("Datos generales", {
            "fields": (
                "titulo",
                "slug",
                "descripcion_corta",
                "descripcion_larga",
                "categoria",
                "linea",
                "tematica_genero",
                "orden",
            )
        }),

        ("Curso asincrónico (opcional)", {
            "fields": ("url_curso",),
        }),

        ("Requisitos y beneficios", {
            "fields": (
                "requisitos",
                "beneficios",
                "bases_pdf",
            ),
        }),

        ("Imagen", {
            "fields": ("imagen",),
        }),

        ("Fechas", {
            "fields": (
                "fecha_inicio",
                "fecha_fin",
            ),
        }),

        ("Jurados / Formadores / Tutores", {
            "fields": (
                "bloque_personas",

                "jurado1_nombre",
                "jurado1_foto",
                "jurado1_bio",

                "jurado2_nombre",
                "jurado2_foto",
                "jurado2_bio",

                "jurado3_nombre",
                "jurado3_foto",
                "jurado3_bio",
            ),
        }),
    )


# ============================================================
#  POSTULACIÓN IDEA
# ============================================================

@admin.register(PostulacionIDEA)
class PostulacionIDEAAdmin(admin.ModelAdmin):

    list_display = (
        "nombre_proyecto",
        "presentante",
        "convocatoria",
        "tipo_proyecto",
        "genero",
        "estado",
        "documentacion_estado",
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

    # --------------------------------------------------
    # PRESENTANTE (Registro Audiovisual)
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

    # --------------------------------------------------
    # EXPORTAR A EXCEL
    # --------------------------------------------------
    def exportar_excel_postulaciones(self, request, queryset):

        wb = Workbook()
        ws = wb.active
        ws.title = "Postulaciones"

        headers = [
            "Fecha postulación",
            "Nombre completo",
            "Edad",
            "Género (persona)",
            "Lugar de residencia",
            "Convocatoria",
            "Tipo de proyecto",
            "Género (proyecto)",
        ]
        ws.append(headers)

        queryset = queryset.select_related("user", "convocatoria")

        for p in queryset:

            nombre = ""
            edad = ""
            genero_persona = ""
            lugar = ""

            ph = getattr(p.user, "persona_humana", None)
            pj = getattr(p.user, "persona_juridica", None)

            if ph:
                nombre = ph.nombre_completo or ""
                edad = ph.edad or ""
                genero_persona = ph.get_genero_display() if ph.genero else ""
                lugar = (
                    ph.otro_lugar_residencia
                    if ph.lugar_residencia == "otro"
                    else ph.get_lugar_residencia_display()
                )

            elif pj:
                nombre = pj.razon_social or ""
                edad = pj.antiguedad or ""
                genero_persona = "—"
                lugar = (
                    pj.otro_lugar_residencia
                    if pj.lugar_residencia == "otro"
                    else pj.get_lugar_residencia_display()
                )

            ws.append([
                p.fecha_envio.strftime("%d/%m/%Y %H:%M"),
                nombre,
                edad,
                genero_persona,
                lugar,
                p.convocatoria.titulo if p.convocatoria else "",
                p.get_tipo_proyecto_display(),
                p.get_genero_display(),
            ])

        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 22

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="postulaciones.xlsx"'
        wb.save(response)

        return response

    exportar_excel_postulaciones.short_description = "Exportar seleccionadas a Excel (.xlsx)"

    # --------------------------------------------------
    # ESTADO DOCUMENTACIÓN
    # --------------------------------------------------
    def documentacion_estado(self, obj):

        tiene_personal = DocumentoPersonal.objects.filter(
            user=obj.user
        ).exists()

        tiene_proyecto = DocumentoProyecto.objects.filter(
            postulacion=obj
        ).exists()

        if tiene_personal and tiene_proyecto:
            color = "#2ecc71"
            texto = "Completa"
        else:
            color = "#e74c3c"
            texto = "Incompleta"

        return format_html(
            '<span style="color:white; padding:3px 6px; background:{}; border-radius:4px;">{}</span>',
            color,
            texto
        )

    documentacion_estado.short_description = "Documentación"


# ============================================================
#  DOCUMENTACIÓN PERSONAL
# ============================================================

@admin.register(DocumentoPersonal)
class DocumentoPersonalAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "archivo_link",
        "fecha_subida",
        "postulaciones_asociadas",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    ordering = ("-fecha_subida",)

    def archivo_link(self, obj):
        return format_html(
            '<a href="{}" download>📄 Descargar</a>',
            obj.archivo.url
        )

    archivo_link.short_description = "Archivo"

    def postulaciones_asociadas(self, obj):
        postulaciones = PostulacionIDEA.objects.filter(user=obj.user)
        if postulaciones.exists():
            return ", ".join(p.nombre_proyecto for p in postulaciones)
        return "—"

    postulaciones_asociadas.short_description = "Postulaciones"


# ============================================================
#  DOCUMENTACIÓN DEL PROYECTO
# ============================================================

@admin.register(DocumentoProyecto)
class DocumentoProyectoAdmin(admin.ModelAdmin):

    list_display = (
        "postulacion",
        "usuario",
        "archivo_link",
        "fecha_subida",
    )

    search_fields = (
        "postulacion__nombre_proyecto",
        "postulacion__user__username",
    )

    ordering = ("-fecha_subida",)

    def usuario(self, obj):
        return obj.postulacion.user.username

    usuario.short_description = "Usuario"

    def archivo_link(self, obj):
        return format_html(
            '<a href="{}" download>📄 Descargar</a>',
            obj.archivo.url
        )

    archivo_link.short_description = "Archivo"


# ============================================================
#  INSCRIPCIÓN A CURSOS
# ============================================================

@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "convocatoria",
        "fecha",
    )

    list_filter = (
        "convocatoria",
    )

    search_fields = (
        "user__username",
        "user__email",
        "convocatoria__titulo",
    )

    ordering = ("-fecha",)
