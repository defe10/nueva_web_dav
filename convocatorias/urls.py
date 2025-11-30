from django.urls import path
from . import views

urlpatterns = [

    # --------------------------
    # HOME
    # --------------------------
    path("", views.convocatorias_home, name="convocatorias_home"),

    # --------------------------
    # LÍNEAS IDEA – Concursos
    # --------------------------
    path("idea/corto-ficcion/", views.idea_concurso_ficcion, name="idea_concurso_ficcion"),
    path("idea/videoclip/", views.idea_concurso_videoclip, name="idea_concurso_videoclip"),

    # --------------------------
    # LÍNEAS IDEA – Programas
    # --------------------------
    path("idea/desarrollo-largometrajes/", views.idea_programa_largometrajes, name="idea_programa_largometrajes"),
    path("idea/laboratorio-cortometrajes/", views.idea_programa_laboratorio, name="idea_programa_laboratorio"),
    path("idea/cine-en-comunidad/", views.idea_programa_comunidad, name="idea_programa_comunidad"),
    path("idea/animacion/", views.idea_programa_animacion, name="idea_programa_animacion"),
    path("idea/videojuegos/", views.idea_programa_videojuegos, name="idea_programa_videojuegos"),

    # --------------------------
    # LÍNEAS IDEA – Subsidios
    # --------------------------
    path("idea/rodaje/", views.idea_subsidio_rodaje, name="idea_subsidio_rodaje"),
    path("idea/finalizacion/", views.idea_subsidio_finalizacion, name="idea_subsidio_finalizacion"),
    path("idea/eventos/", views.idea_subsidio_eventos, name="idea_subsidio_eventos"),

    # --------------------------
    # CURSOS Y CAPACITACIONES
    # --------------------------
    path("idea/curso-presupuestos/", views.idea_curso_presupuestos, name="idea_curso_presupuestos"),
    path("idea/curso-contar/", views.idea_curso_contar, name="idea_curso_contar"),

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

]


