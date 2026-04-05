from django.contrib import admin
from .models import Nodo, Opcion, PalabraClave


class OpcionInline(admin.TabularInline):
    model = Opcion
    fk_name = "nodo_origen"
    extra = 1


@admin.register(Nodo)
class NodoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "es_inicio", "activo")
    list_filter = ("es_inicio", "activo")
    search_fields = ("nombre", "slug", "mensaje")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("texto", "nodo_origen", "nodo_destino", "orden")
    list_filter = ("nodo_origen",)
    search_fields = ("texto",)
    ordering = ("nodo_origen", "orden")


@admin.register(PalabraClave)
class PalabraClaveAdmin(admin.ModelAdmin):
    list_display = ("texto", "nodo_destino", "prioridad", "activo", "longitud_texto")
    list_filter = ("activo", "nodo_destino", "prioridad")
    search_fields = ("texto", "nodo_destino__nombre")
    ordering = ("-prioridad", "texto")

    def longitud_texto(self, obj):
        return len(obj.texto)
    longitud_texto.short_description = "Longitud"