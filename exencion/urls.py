from django.urls import path
from . import views

app_name = "exencion"

urlpatterns = [
    path("iniciar/", views.iniciar_solicitud, name="iniciar"),
    path("iniciar/<int:convocatoria_id>/", views.iniciar_solicitud, name="iniciar_convocatoria"),

    path("documentacion/<int:exencion_id>/", views.subir_documentacion, name="documentacion"),
    path("completada/<int:exencion_id>/", views.solicitud_completada, name="completada"),
]
