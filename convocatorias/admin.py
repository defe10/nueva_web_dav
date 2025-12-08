from django.contrib import admin
from django.utils.html import format_html

from .models import Convocatoria, PostulacionIDEA, DocumentoPersonal, DocumentoProyecto


# ============================================================
#  CONVOCATORIA
# ============================================================

@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "linea", "fecha_inicio", "fecha_fin", "vigente", "orden")
    list_filter = ("categoria", "linea", "fecha_inicio", "fecha_fin")
    search_fields = ("titulo", "descripcion_corta", "descripcion_larga")
    prepopulated_fields = {"slug": ("titulo",)}
    ordering = ("orden", "-fecha_inicio")


# ============================================================
#  POSTULACIÓN IDEA
# ============================================================

@admin.register(PostulacionIDEA)
class PostulacionIDEAAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_proyecto",
        "user",
        "convocatoria",
        "tipo_proyecto",
        "genero",
        "estado",
        "documentacion_estado",
        "fecha_envio",
    )
    list_filter = ("estado", "tipo_proyecto", "genero", "convocatoria")
    search_fields = ("nombre_proyecto", "user__username", "user__email")
    ordering = ("-fecha_envio",)

    # ---- Estado de documentación personal + proyecto ----
    def documentacion_estado(self, obj):
        tiene_personal = DocumentoPersonal.objects.filter(user=obj.user).exists()
        tiene_proyecto = DocumentoProyecto.objects.filter(postulacion=obj).exists()

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
    list_display = ("user", "archivo_link", "fecha_subida", "postulaciones_asociadas")
    search_fields = ("user__username", "user__email")
    ordering = ("-fecha_subida",)

    def archivo_link(self, obj):
        return format_html('<a href="{}" download>📄 Descargar</a>', obj.archivo.url)

    archivo_link.short_description = "Archivo"

    def postulaciones_asociadas(self, obj):
        postulaciones = PostulacionIDEA.objects.filter(user=obj.user)
        if postulaciones.exists():
            return ", ".join([p.nombre_proyecto for p in postulaciones])
        return "—"

    postulaciones_asociadas.short_description = "Postulaciones"


# ============================================================
#  DOCUMENTACIÓN DEL PROYECTO
# ============================================================

@admin.register(DocumentoProyecto)
class DocumentoProyectoAdmin(admin.ModelAdmin):
    list_display = ("postulacion", "usuario", "archivo_link", "fecha_subida")
    search_fields = ("postulacion__nombre_proyecto", "postulacion__user__username")
    ordering = ("-fecha_subida",)

    def usuario(self, obj):
        return obj.postulacion.user.username

    usuario.short_description = "Usuario"

    def archivo_link(self, obj):
        return format_html('<a href="{}" download>📄 Descargar</a>', obj.archivo.url)

    archivo_link.short_description = "Archivo"
