from django.contrib import admin
from .models import PersonaHumana, PersonaJuridica
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse


# ============================================================
# ACCIÓN GLOBAL — EXPORTAR A EXCEL (CSV)
# ============================================================

def exportar_excel(modeladmin, request, queryset):
    """
    Exporta los registros seleccionados a un archivo XLSX real.
    """

    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Datos"

    # Obtener todos los campos del modelo
    campos = [field.name for field in modeladmin.model._meta.fields]

    # Escribir encabezados
    for col, campo in enumerate(campos, start=1):
        ws.cell(row=1, column=col, value=campo)

    # Escribir datos
    for row, obj in enumerate(queryset, start=2):
        for col, campo in enumerate(campos, start=1):
            valor = getattr(obj, campo)

            # Si es fecha u objeto complejo → convertir a string
            if callable(valor):
                valor = valor()
            if valor is None:
                valor = ""
                
            ws.cell(row=row, column=col, value=str(valor))

    # Preparar respuesta HTTP
    nombre = modeladmin.model.__name__.lower()

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}.xlsx"'
        },
    )

    wb.save(response)
    return response


exportar_excel.short_description = "📤 Exportar selección a Excel (.xlsx)"


# ============================================================
# PERSONA HUMANA
# ============================================================

@admin.register(PersonaHumana)
class PersonaHumanaAdmin(admin.ModelAdmin):

    actions = [exportar_excel]

    list_display = (
        "id",
        "user",
        "fecha_creacion",
        "nombre_completo",
        "cuil_cuit",
        "fecha_nacimiento",
        "edad",
        "genero",
        "lugar_residencia",
        "otro_lugar_residencia",
        "nivel_educativo",
        "domicilio_real",
        "telefono",
        "email",
        "situacion_iva",
        "actividad_dgr",
        "domicilio_fiscal",
        "area_desempeno_1",
        "area_desempeno_2",
        "area_cultural",
        "link_1",
        "link_2",
        "link_3",
    )

    search_fields = ("nombre_completo", "cuil_cuit", "email", "telefono")

    list_filter = (
        "genero",
        "lugar_residencia",
        "nivel_educativo",
        "situacion_iva",
        "actividad_dgr",
        "fecha_creacion",
    )

    ordering = ("-fecha_creacion",)

    fieldsets = (
        ("🔹 Datos Personales", {
            "fields": (
                "user",
                "nombre_completo",
                ("cuil_cuit", "fecha_nacimiento", "edad"),
                "genero",
                ("lugar_residencia", "otro_lugar_residencia"),
                "nivel_educativo",
                "domicilio_real",
                ("telefono", "email"),
            )
        }),

        ("🔹 Datos Fiscales", {
            "fields": (
                "situacion_iva",
                "actividad_dgr",
                "domicilio_fiscal",
            )
        }),

        ("🔹 Datos Profesionales", {
            "fields": (
                "area_desempeno_1",
                "area_desempeno_2",
                "area_cultural",
                "link_1",
                "link_2",
                "link_3",
            )
        }),

        ("🔹 Metadatos", {
            "fields": ("fecha_creacion",)
        }),
    )

    readonly_fields = ("fecha_creacion",)


# ============================================================
# PERSONA JURÍDICA
# ============================================================

@admin.register(PersonaJuridica)
class PersonaJuridicaAdmin(admin.ModelAdmin):

    actions = [exportar_excel]

    list_display = (
        "id",
        "user",
        "razon_social",
        "nombre_comercial",
        "cuil_cuit",
        "tipo_persona_juridica",
        "domicilio_fiscal",
        "lugar_residencia",
        "otro_lugar_residencia",
        "fecha_constitucion",
        "antiguedad",
        "email",
        "telefono",
        "situacion_iva",
        "actividad_dgr",
        "area_desempeno_JJPP_1",
        "area_desempeno_JJPP_2",
        "link_1",
        "link_2",
        "link_3",
        "fecha_creacion",
    )

    search_fields = ("razon_social", "cuil_cuit", "email", "telefono")

    list_filter = (
        "tipo_persona_juridica",
        "lugar_residencia",
        "situacion_iva",
        "actividad_dgr",
        "fecha_constitucion",
    )

    ordering = ("-fecha_creacion",)

    fieldsets = (
        ("🔹 Datos Jurídicos", {
            "fields": (
                "user",
                "tipo_persona_juridica",
                "razon_social",
                "nombre_comercial",
                ("cuil_cuit", "fecha_constitucion", "antiguedad"),
            )
        }),

        ("🔹 Contacto y Domicilio", {
            "fields": (
                "domicilio_fiscal",
                ("lugar_residencia", "otro_lugar_residencia"),
                "email",
                "telefono",
            )
        }),

        ("🔹 Datos Fiscales", {
            "fields": (
                "situacion_iva",
                "actividad_dgr",
            )
        }),

        ("🔹 Actividad Audiovisual", {
            "fields": (
                "area_desempeno_JJPP_1",
                "area_desempeno_JJPP_2",
                "link_1",
                "link_2",
                "link_3",
            )
        }),

        ("🔹 Metadatos", {
            "fields": ("fecha_creacion",)
        }),
    )

    readonly_fields = ("fecha_creacion",)
