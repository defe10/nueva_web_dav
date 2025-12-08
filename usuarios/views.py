from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User

# Formularios
from .forms import LoginForm, RegistroUsuarioForm

# Para emails y activación
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

# Modelos de registro audiovisual
from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from django.contrib.auth.decorators import login_required

# ============================================================
# LOGOUT
# ============================================================

def logout_usuario(request):
    logout(request)
    return redirect("inicio")


# ============================================================
# REGISTRO DE USUARIO
# ============================================================

def registro(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            usuario = form.save()  # Usuario se crea inactivo

            # Email de activación
            current_site = get_current_site(request)
            subject = "Confirmá tu cuenta"

            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)

            html_message = render_to_string("usuarios/email_confirmacion.html", {
                "user": usuario,
                "domain": current_site.domain,
                "uid": uid,
                "token": token,
            })

            text_message = f"""
Hola {usuario.username},

Hacé clic en este enlace para activar tu cuenta:

https://{current_site.domain}/usuarios/activar/{uid}/{token}/
"""

            email = EmailMultiAlternatives(
                subject,
                text_message,
                "noresponder@registrosalta.ar",
                [usuario.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            messages.success(request, "Tu cuenta fue creada. Revisá tu correo para activarla.")
            return redirect("usuario:login")

    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})


# ============================================================
# LOGIN
# ============================================================

def login_usuario(request):

    next_url = request.GET.get("next") or request.POST.get("next")

    # Normalizar valores inválidos
    if next_url in [None, "", "None", "null", "undefined"]:
        next_url = None

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                messages.error(request, "Tu cuenta aún no está activada. Revisá tu correo.")
                return redirect("usuario:login")

            login(request, user)

            # Redirección segura
            if next_url:
                if next_url.startswith("/"):
                    return redirect(next_url)

            return redirect("inicio")

    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {
        "form": form,
        "next": next_url,
    })



# ============================================================
# ACTIVAR CUENTA
# ============================================================

def activar_cuenta(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        usuario = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        usuario = None

    if usuario and default_token_generator.check_token(usuario, token):
        usuario.is_active = True
        usuario.save()
        messages.success(request, "Tu cuenta fue activada. Ya podés iniciar sesión.")
        return redirect("usuario:login")

    messages.error(request, "El enlace de activación no es válido o ya expiró.")
    return redirect("usuario:login")


# ============================================================
# PANEL DEL USUARIO
# ============================================================

@login_required(login_url="/usuarios/login/")
def panel_usuario(request):
    user = request.user

    # Recuperar registros si existen
    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    # Si tiene registro → mostrar panel.html
    if persona_humana or persona_juridica:
        return render(
            request,
            "usuarios/panel.html",   # O "registro/panel.html", lo que uses
            {
                "persona_humana": persona_humana,
                "persona_juridica": persona_juridica,
            }
        )

    # Si no tiene nada → enviarlo a elegir tipo
    return redirect("registro_audiovisual:seleccionar_tipo_registro")