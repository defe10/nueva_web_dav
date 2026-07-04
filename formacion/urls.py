from django.urls import path
from . import views

app_name = "formacion"

urlpatterns = [
    path("crear/",                     views.crear_convocatoria_formacion, name="crear_convocatoria"),
    path("<slug:slug>/",               views.detalle,                      name="detalle"),
    path("inscribirse/<int:convocatoria_id>/", views.inscribirse,          name="inscribirse"),
]
