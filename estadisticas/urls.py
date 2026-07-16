from django.urls import path
from . import views

app_name = "estadisticas"

urlpatterns = [
    path("",            views.dashboard, name="dashboard"),
    path("exportar/",   views.exportar, name="exportar"),
    path("registro/",   views.dashboard_registro, name="dashboard_registro"),
    path("registro/exportar/",   views.exportar_registro, name="exportar_registro"),
    path("exenciones/", views.dashboard_exencion, name="dashboard_exencion"),
    path("exenciones/exportar/", views.exportar_exenciones, name="exportar_exenciones"),
    path("formacion/",  views.dashboard_formacion, name="dashboard_formacion"),
    path("formacion/exportar/",  views.exportar_formacion, name="exportar_formacion"),
]
