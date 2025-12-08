from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User

# Formularios
from .forms import LoginForm, RegistroUsuarioForm

# Para emails y activación
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

from django.contrib.auth import logout
from django.utils.http import urlsafe_base64_decode

def logout_usuario(request):
    logout(request)
    return redirect("inicio")   # ajustá según tu URL de inicio real

# ===========================
#   REGISTRO
# ===========================
def registro(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            usuario = form.save()  # Usuario se crea inactivo

            # ---- Email de activación ----
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
            # ------------------------------

            messages.success(request, "Tu cuenta fue creada. Revisá tu correo para activarla.")
            return redirect("usuario:login")

    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})


# ===========================
#   LOGIN
# ===========================
def login_usuario(request):

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                messages.error(request, "Tu cuenta aún no está activada. Revisá tu correo.")
                return redirect("usuario:login")

            login(request, user)

            # --- redirección segura ---
            if next_url:
                if next_url.startswith("/"):
                    return redirect(next_url)
                else:
                    try:
                        return redirect(next_url)
                    except:
                        pass

            return redirect("inicio")

    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {
        "form": form,
        "next": next_url,
    })
# ===========================
#   ACTIVAR CUENTA
# ===========================


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
