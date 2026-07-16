from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Nodo, Opcion, PalabraClave, ConfiguracionChatbot, ConsultaLog


# ============================================================
# NODO
# ============================================================
class OpcionInline(admin.TabularInline):
    model = Opcion
    fk_name = "nodo_origen"
    extra = 1


@admin.register(Nodo)
class NodoAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "slug", "es_inicio", "activo", "cant_opciones", "alerta_huerfano")
    list_filter   = ("es_inicio", "activo")
    search_fields = ("nombre", "slug", "mensaje")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [OpcionInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _cant_opciones=Count("opciones", distinct=True),
            _como_destino=Count("opcion", distinct=True),
        )

    def cant_opciones(self, obj):
        return obj._cant_opciones
    cant_opciones.short_description = "Opciones"
    cant_opciones.admin_order_field = "_cant_opciones"

    def alerta_huerfano(self, obj):
        # G: nodo sin opciones salientes y sin opciones entrantes (ni es inicio)
        sin_salida  = obj._cant_opciones == 0
        sin_entrada = obj._como_destino == 0
        if not obj.es_inicio and sin_entrada:
            return format_html('<span title="Nadie lleva a este nodo">⚠️ Sin entrada</span>')
        if sin_salida and not obj.es_inicio:
            return format_html('<span title="Nodo terminal (sin opciones salientes)">🔚 Terminal</span>')
        return "—"
    alerta_huerfano.short_description = "Alerta"


# ============================================================
# OPCIÓN
# ============================================================
@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display  = ("texto", "nodo_origen", "nodo_destino", "orden")
    list_filter   = ("nodo_origen",)
    search_fields = ("texto",)
    ordering      = ("nodo_origen", "orden")


# ============================================================
# PALABRA CLAVE
# ============================================================
@admin.register(PalabraClave)
class PalabraClaveAdmin(admin.ModelAdmin):
    list_display  = ("texto", "nodo_destino", "prioridad", "activo", "longitud_texto")
    list_filter   = ("activo", "nodo_destino", "prioridad")
    search_fields = ("texto", "nodo_destino__nombre")
    ordering      = ("-prioridad", "texto")

    def longitud_texto(self, obj):
        return len(obj.texto)
    longitud_texto.short_description = "Longitud"


# ============================================================
# CONFIGURACIÓN (singleton)
# ============================================================
@admin.register(ConfiguracionChatbot)
class ConfiguracionChatbotAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("mensaje_no_encontrado",),
            "description": (
                "Solo puede existir una configuración. "
                "Si no existe, el sistema usa el mensaje por defecto."
            ),
        }),
    )

    def has_add_permission(self, request):
        return not ConfiguracionChatbot.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# LOG DE CONSULTAS
# ============================================================
@admin.register(ConsultaLog)
class ConsultaLogAdmin(admin.ModelAdmin):
    list_display  = ("fecha", "texto_consulta", "encontrado", "keyword_matcheada", "nodo_destino")
    list_filter   = ("encontrado", "nodo_destino", "fecha")
    search_fields = ("texto_consulta", "keyword_matcheada")
    ordering      = ("-fecha",)
    date_hierarchy = "fecha"
    readonly_fields = ("fecha", "texto_consulta", "keyword_matcheada", "nodo_destino", "encontrado")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
