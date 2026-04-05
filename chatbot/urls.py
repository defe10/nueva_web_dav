from django.urls import path
from .views import inicio_chatbot, ver_nodo, volver, buscar_consulta, widget_chatbot

urlpatterns = [
    path("", inicio_chatbot, name="chatbot_inicio"),
    path("opcion/<int:opcion_id>/", ver_nodo, name="ver_nodo"),
    path("volver/", volver, name="chatbot_volver"),
    path("buscar/", buscar_consulta, name="chatbot_buscar"),
    path("widget/", widget_chatbot, name="chatbot_widget"),
]