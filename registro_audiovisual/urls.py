from django.urls import path
from . import views

app_name = "registro"

urlpatterns = [
    path("seleccionar-tipo/", views.seleccionar_tipo_registro, name="seleccionar_tipo_registro"),

    path("persona-humana/", views.editar_persona_humana, name="editar_persona_humana"),
    path("persona-juridica/", views.editar_persona_juridica, name="editar_persona_juridica"),

    path("inscripcion-exitosa/", views.inscripcion_exitosa, name="inscripcion_exitosa"),
]
