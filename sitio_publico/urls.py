from django.urls import path
from . import views

app_name = "sitio_publico"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("institucional/", views.institucional, name="institucional"),
    path("programas/", views.programas, name="programas"),
]
