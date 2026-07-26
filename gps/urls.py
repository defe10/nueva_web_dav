from django.urls import path

from . import views

app_name = "gps"

urlpatterns = [
    # Panel del titular
    path("", views.mis_obras, name="mis_obras"),
    path("obra/nueva/", views.obra_crear, name="obra_crear"),
    path("obra/<int:pk>/", views.obra_detalle, name="obra_detalle"),
    path("obra/<int:pk>/editar/", views.obra_editar, name="obra_editar"),
    path("obra/<int:obra_pk>/ficha/", views.ficha_editar, name="ficha_editar"),

    # Autocompletado de vínculo con el Registro Audiovisual
    path("api/registro/buscar/", views.registro_buscar, name="registro_buscar"),

    # Sistema +Hito
    path("obra/<int:obra_pk>/hito/nuevo/", views.hito_crear, name="hito_crear"),
    path("hito/<int:pk>/editar/", views.hito_editar, name="hito_editar"),
    path("hito/<int:pk>/eliminar/", views.hito_eliminar, name="hito_eliminar"),
]
