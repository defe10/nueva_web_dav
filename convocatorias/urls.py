from django.urls import path
from . import views

urlpatterns = [

    # --------------------------
    # HOME
    # --------------------------
    path("", views.convocatorias_home, name="convocatorias_home"),

   
    # --------------------------
    # POSTULACIÓN IDEA
    # --------------------------
    path("idea/postular/", views.postular_idea, name="postular_idea"),
    path("idea/documentacion-personal/", views.subir_documentacion_personal, name="subir_documentacion_personal"),
    path("idea/documentacion-proyecto/<int:postulacion_id>/",
         views.subir_documentacion_proyecto, name="subir_documentacion_proyecto"),
    path("idea/confirmar/<int:postulacion_id>/",
         views.confirmar_postulacion_idea, name="confirmar_postulacion_idea"),
    path("idea/confirmada/", views.postulacion_idea_confirmada, name="postulacion_idea_confirmada"),

    # DEL FORMULARIO WEB CONVOCATORAS

    path("crear/", views.crear_convocatoria, name="crear_convocatoria"),

    path("<slug:slug>/", views.convocatoria_detalle, name="convocatoria_detalle"),



]


