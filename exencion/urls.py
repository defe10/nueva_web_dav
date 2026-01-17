from django.urls import path
from . import views

app_name = "exencion"

urlpatterns = [

    # --------------------------------
    # INICIAR SOLICITUD
    # --------------------------------
    path(
        "iniciar/",
        views.iniciar_solicitud,
        name="iniciar"
    ),
    path(
        "iniciar/<int:convocatoria_id>/",
        views.iniciar_solicitud,
        name="iniciar_convocatoria"
    ),

    # --------------------------------
    # DOCUMENTACIÓN INICIAL (pantalla)
    # --------------------------------
    path(
        "documentacion/<int:exencion_id>/",
        views.subir_documentacion,
        name="documentacion"
    ),

    # AGREGAR DOCUMENTOS INICIALES (pendiente)
    path(
        "documentacion/<int:exencion_id>/agregar/",
        views.agregar_documentacion,
        name="agregar_documentacion"
    ),

    # CONFIRMAR ENVÍO DOCUMENTACIÓN INICIAL
    path(
        "documentacion/<int:exencion_id>/confirmar/",
        views.confirmar_documentacion,
        name="confirmar_documentacion"
    ),

    # --------------------------------
    # ELIMINAR DOCUMENTO (inicial o subsanado)
    # --------------------------------
    path(
        "documento/<int:documento_id>/eliminar/",
        views.eliminar_documento,
        name="eliminar_documento"
    ),

    # --------------------------------
    # SUBSANACIÓN (pantalla)
    # --------------------------------
    path(
        "subsanar/<int:exencion_id>/",
        views.subir_documento_subsanado_exencion,
        name="subir_documento_subsanado_exencion"
    ),

    # AGREGAR DOCUMENTOS SUBSANADOS (pendiente)
    path(
        "subsanar/<int:exencion_id>/agregar/",
        views.agregar_documento_subsanado_exencion,
        name="agregar_documento_subsanado_exencion"
    ),

    # CONFIRMAR ENVÍO SUBSANACIÓN
    path(
        "subsanar/<int:exencion_id>/confirmar/",
        views.confirmar_documento_subsanado_exencion,
        name="confirmar_documento_subsanado_exencion"
    ),

    # --------------------------------
    # SOLICITUD COMPLETADA
    # --------------------------------
    path(
        "completada/<int:exencion_id>/",
        views.solicitud_completada,
        name="completada"
    ),
]
