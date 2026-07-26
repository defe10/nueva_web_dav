from django.contrib import admin

from .forms import ObraAdminForm
from .models import Obra, Hito, FichaTecnica, TituloAnterior


class FichaTecnicaInline(admin.StackedInline):
    model = FichaTecnica
    extra = 0
    can_delete = True


class TituloAnteriorInline(admin.TabularInline):
    model = TituloAnterior
    extra = 0
    fields = ("titulo", "anio_hasta", "nota", "automatico")
    readonly_fields = ("automatico",)


class HitoInline(admin.TabularInline):
    model = Hito
    fk_name = "obra"
    extra = 0
    fields = ("tipo", "nombre", "anio", "entidad", "estado", "resultado", "verificado")
    show_change_link = True


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    form = ObraAdminForm
    list_display = (
        "titulo", "owner", "formato",
        "estado_produccion", "seguimiento", "verificado", "fecha_actualizacion",
    )
    list_filter = (
        "estado_produccion", "seguimiento", "formato", "verificado", "anio_inicio",
    )
    # Se busca también por el título viejo: la obra pudo haber cambiado de nombre.
    search_fields = (
        "titulo", "titulos_anteriores__titulo",
        "direccion", "produccion", "owner__username",
    )
    list_select_related = ("owner",)
    # La titularidad se traspasa: una obra que arrancó a nombre del productor
    # puede terminar en manos del director. Con autocomplete se busca por
    # nombre o mail en vez de scrollear todos los usuarios.
    autocomplete_fields = ("owner",)
    filter_horizontal = ("postulaciones",)
    inlines = [TituloAnteriorInline, FichaTecnicaInline, HitoInline]


@admin.register(Hito)
class HitoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "tipo", "obra", "anio",
        "entidad", "estado", "resultado", "verificado",
    )
    list_filter = ("tipo", "estado", "verificado", "anio")
    search_fields = ("nombre", "entidad", "resultado", "obra__titulo")
    autocomplete_fields = ("obra", "hito_origen")
    readonly_fields = ("creado_por",)
