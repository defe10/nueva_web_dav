from django.contrib import admin
from .models import Convocatoria

@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fecha_inicio", "fecha_fin", "vigente")
    list_filter = ("fecha_inicio", "fecha_fin")
    search_fields = ("titulo", "descripcion_corta")
    prepopulated_fields = {"slug": ("titulo",)}
