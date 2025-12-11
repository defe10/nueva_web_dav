from django.urls import path
from . import views

app_name = "exencion"

urlpatterns = [
    path("iniciar/<int:convocatoria_id>/", views.iniciar_solicitud, name="iniciar"),
    path("documentacion/<int:solicitud_id>/", views.subir_documentacion, name="documentacion"),
    path("completada/<int:solicitud_id>/", views.solicitud_completada, name="completada"),
]
