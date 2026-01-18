from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("nomina/", views.nomina_registro, name="nomina_registro"),
    path("nomina/excel/", views.nomina_registro_excel, name="nomina_registro_excel"),
]
