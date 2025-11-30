from django.urls import path
from . import views

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_usuario, name="login"),
    path("logout/", views.logout_usuario, name="logout"),
    path("panel/", views.panel_usuario, name="panel_usuario"),
    path('registrar/', views.registrar_usuario, name='registrar_usuario')

]
