from django.urls import path
from . import views

app_name = "convocatorias"

urlpatterns = [

    # --------------------------------
    # HOME DE CONVOCATORIAS
    # --------------------------------
    path(
        "",
        views.convocatorias_home,
        name="convocatorias_home"
    ),

    # --------------------------------
    # INSCRIBIRSE A UNA CONVOCATORIA
    # (decide flujo según la línea)
    # --------------------------------
    path(
        "<slug:slug>/inscribirse/",
        views.inscribirse_convocatoria,
        name="inscribirse_convocatoria"
    ),

    # --------------------------------
    # FORMULARIO DE POSTULACIÓN (PASO 1)
    # --------------------------------
    path(
        "postular/<int:convocatoria_id>/",
        views.postular_convocatoria,
        name="postular_convocatoria"
    ),

    # --------------------------------
    # DOCUMENTACIÓN PERSONAL (PASO 2)
    # --------------------------------
    path(
        "documentacion/personal/<int:postulacion_id>/",
        views.subir_documentacion_personal,
        name="subir_documentacion_personal"
    ),

    # --------------------------------
    # DOCUMENTACIÓN DEL PROYECTO (PASO 3)
    # --------------------------------
    path(
        "documentacion/proyecto/<int:postulacion_id>/",
        views.subir_documentacion_proyecto,
        name="subir_documentacion_proyecto"
    ),

    # --------------------------------
    # POSTULACIÓN COMPLETADA (PASO FINAL)
    # --------------------------------
    path(
        "postulacion/enviada/<int:postulacion_id>/",
        views.postulacion_confirmada,
        name="postulacion_confirmada"
    ),

    # --------------------------------
    # CREAR CONVOCATORIA (ADMIN)
    # --------------------------------
    path(
        "crear/",
        views.crear_convocatoria,
        name="crear_convocatoria"
    ),

    # --------------------------------
    # DETALLE DE LA CONVOCATORIA
    # SIEMPRE ÚLTIMO
    # --------------------------------
    path(
        "<slug:slug>/",
        views.convocatoria_detalle,
        name="convocatoria_detalle"
    ),
]
