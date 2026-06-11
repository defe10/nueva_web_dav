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
    # SUBSANACIÓN DE DOCUMENTACIÓN (pantalla)
    # --------------------------------
    path(
        "subsanar/<int:postulacion_id>/",
        views.subir_documento_subsanado,
        name="subir_documento_subsanado"
    ),
    path(
        "subsanar/<int:postulacion_id>/agregar/",
        views.agregar_documento_subsanado,
        name="agregar_documento_subsanado"
    ),
    path(
        "subsanar/<int:postulacion_id>/confirmar/",
        views.confirmar_documento_subsanado,
        name="confirmar_documento_subsanado"
    ),

    # --------------------------------
    # INSCRIBIRSE A UNA CONVOCATORIA
    # --------------------------------
    path(
        "<slug:slug>/inscribirse/",
        views.inscribirse_convocatoria,
        name="inscribirse_convocatoria"
    ),

    # --------------------------------
    # WIZARD DE POSTULACIÓN (nuevo flujo)
    # --------------------------------
    path(
        "postular/<int:convocatoria_id>/",
        views.wizard_inicio,
        name="postular_convocatoria",   # alias para no romper links existentes
    ),
    path(
        "postular/<int:postulacion_id>/<str:paso>/",
        views.wizard_paso,
        name="wizard_paso",
    ),
    path(
        "postular/<int:postulacion_id>/doc-integrante/<str:rol>/",
        views.subir_doc_integrante,
        name="subir_doc_integrante",
    ),

    # --------------------------------
    # ELIMINAR DOCUMENTO
    # --------------------------------
    path(
        "documento/<int:documento_id>/eliminar/",
        views.eliminar_documento_postulacion,
        name="eliminar_documento_postulacion"
    ),

    # --------------------------------
    # POSTULACIÓN COMPLETADA
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
    # VER DOCUMENTACIÓN (USUARIO)
    # --------------------------------
    path(
        "ver-documentacion/<int:postulacion_id>/",
        views.ver_documentacion_proyecto,
        name="ver_documentacion_proyecto"
    ),

    # --------------------------------
    # ✅ RENDICIÓN (DETALLE)
    # --------------------------------
    path(
        "rendicion/<int:rendicion_id>/",
        views.rendicion_detalle,
        name="rendicion_detalle"
    ),

    # --------------------------------
    # DETALLE DE CONVOCATORIA (SIEMPRE ÚLTIMO)
    # --------------------------------
    path(
        "<slug:slug>/",
        views.convocatoria_detalle,
        name="convocatoria_detalle"
    ),
]
