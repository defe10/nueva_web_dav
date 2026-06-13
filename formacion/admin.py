from django.contrib import admin
from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from .models import InscripcionFormacion, ConfiguracionInscripcionFormacion


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
    search_fields = (
        "user__username",
        "user__email",
        "nombre",
        "apellido",
        "dni",
        "email",
        "telefono",
    )
    ordering = ("-fecha",)
    actions = [
        marcar_admitido,
        marcar_no_admitido,
        marcar_lista_espera,
        "exportar_excel",
    ]
    readonly_fields = ("user", "convocatoria", "fecha")
    fieldsets = (
        ("Sistema", {"fields": ("user", "convocatoria", "estado", "fecha")}),
        ("Registro Audiovisual", {"fields": ("persona_humana", "persona_juridica")}),
        ("Contacto", {"fields": ("nombre", "apellido", "dni", "email", "telefono", "localidad", "otra_localidad")}),
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

    def exportar_excel(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Formación"

        headers = [
            "Fecha", "Usuario", "Convocatoria", "Estado",
            "Email", "Teléfono", "Vínculo con el sector",
            "Nombre", "Apellido", "DNI", "Localidad",
            "Tiene Registro Audiovisual",
        ]
        ws.append(headers)

        qs = queryset.select_related(
            "user", "convocatoria", "persona_humana", "persona_juridica"
        )
        for ins in qs:
            tiene_registro = bool(ins.persona_humana_id or ins.persona_juridica_id)
            ws.append([
                ins.fecha.strftime("%d/%m/%Y %H:%M") if ins.fecha else "",
                ins.user.username,
                ins.convocatoria.titulo if ins.convocatoria else "",
                ins.get_estado_display(),
                ins.user.email or ins.email or "",
                self.contacto_telefono(ins),
                ins.get_vinculo_sector_display() if ins.vinculo_sector else "",
                ins.nombre or "",
                ins.apellido or "",
                ins.dni or "",
                ins.get_localidad_display() if ins.localidad else "",
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

    exportar_excel.short_description = "📤 Exportar seleccionadas a Excel (.xlsx)"


@admin.register(ConfiguracionInscripcionFormacion)
class ConfiguracionInscripcionFormacionAdmin(admin.ModelAdmin):
    list_display = ("convocatoria",)
    fieldsets = (
        (None, {"fields": ("convocatoria",)}),
        ("Campos del formulario", {"fields": (
            "mostrar_nombre_apellido",
            "mostrar_dni",
            "mostrar_genero",
            "mostrar_edad",
            "mostrar_telefono",
            "mostrar_email",
            "mostrar_documentacion",
        )}),
    )
