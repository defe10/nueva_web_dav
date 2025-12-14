from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views
from .forms import PasswordResetEmailForm

app_name = "usuarios"


urlpatterns = [
    # ----------------------------------
    # Registro / Login / Logout
    # ----------------------------------
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_usuario, name="login"),
    path("logout/", views.logout_usuario, name="logout"),

    # ----------------------------------
    # Panel de usuario
    # ----------------------------------
    path("panel/", views.panel_usuario, name="panel_usuario"),

    # ----------------------------------
    # Activación de cuenta
    # ----------------------------------
    path(
        "activar/<uidb64>/<token>/",
        views.activar_cuenta,
        name="activar"
    ),
]


# ----------------------------------
# Recuperación de contraseña
# ----------------------------------
urlpatterns += [
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/password_reset.html",
            email_template_name="usuarios/password_reset_email.html",
            subject_template_name="usuarios/password_reset_subject.txt",
            form_class=PasswordResetEmailForm,
            success_url=reverse_lazy("usuarios:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password_reset_done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/password_reset_confirm.html",
            success_url=reverse_lazy("usuarios:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
