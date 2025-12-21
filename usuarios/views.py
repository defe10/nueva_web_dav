from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

# Formularios
from .forms import LoginForm, RegistroUsuarioForm

# Email y activación
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

# Modelos
from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from exencion.models import Exencion
from convocatorias.models import Postulacion, AsignacionJuradoConvocatoria


    
# ============================================================
# LOGOUT
# ============================================================

def logout_usuario(request):
    logout(request)
    return redirect("/")


# ============================================================
# REGISTRO DE USUARIO
# (solo usuarios comunes, NO jurados)
# ============================================================

def registro(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.is_active = False
            usuario.save()

            current_site = get_current_site(request)
            subject = "Confirmá tu cuenta"

            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)

            context = {
                "user": usuario,
                "domain": current_site.domain,
                "uid": uid,
                "token": token,
            }

            html_message = render_to_string(
                "usuarios/email_confirmacion.html",
                context
            )

            text_message = (
                f"Hola {usuario.username},\n\n"
                f"Hacé clic en este enlace para activar tu cuenta:\n\n"
                f"https://{current_site.domain}/usuarios/activar/{uid}/{token}/"
            )

            email = EmailMultiAlternatives(
                subject,
                text_message,
                "noresponder@registrosalta.ar",
                [usuario.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            messages.success(
                request,
                "Tu cuenta fue creada. Revisá tu correo para activarla."
            )
            return redirect("usuarios:login")

    else:
        form = RegistroUsuarioForm()

    return render(
        request,
        "usuarios/registro.html",
        {"form": form},
    )


# ============================================================
# LOGIN
# ============================================================

@ratelimit(key="ip", rate="5/m", block=True)
def login_usuario(request):
    next_url = request.GET.get("next") or request.POST.get("next")

    if next_url in [None, "", "None", "null", "undefined"]:
        next_url = None

    try:
        if request.method == "POST":
            form = LoginForm(request, data=request.POST)

            if form.is_valid():
                user = form.get_user()

                if not user.is_active:
                    messages.error(
                        request,
                        "Tu cuenta aún no está activada. Revisá tu correo."
                    )
                    return redirect("usuarios:login")

                login(request, user)

                if next_url and next_url.startswith("/"):
                    return redirect(next_url)

                return redirect("usuarios:redireccion_post_login")
        else:
            form = LoginForm()

    except Ratelimited:
        messages.error(
            request,
            "Se superó el número máximo de intentos de inicio de sesión. "
            "Por favor, intentá nuevamente en unos minutos."
        )
        return redirect("usuarios:login")

    return render(
        request,
        "usuarios/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


# ============================================================
# ACTIVACIÓN DE CUENTA
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
        messages.success(
            request,
            "Tu cuenta fue activada. Ya podés iniciar sesión."
        )
        return redirect("usuarios:login")

    messages.error(
        request,
        "El enlace de activación no es válido o ya expiró."
    )
    return redirect("usuarios:login")


# ============================================================
# REDIRECCIÓN POST LOGIN (CLAVE)
# ============================================================


@login_required(login_url="/usuarios/login/")
def redireccion_post_login(request):
    return redirect("sitio_publico:inicio")



# ============================================================
# PANEL DE USUARIO COMÚN
# ============================================================

@login_required(login_url="/usuarios/login/")
def panel_usuario(request):
    user = request.user

    # ----------------------------------
    # Registro audiovisual
    # ----------------------------------
    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    # ----------------------------------
    # Última exención
    # ----------------------------------
    exencion = (
        Exencion.objects
        .filter(user=user)
        .order_by("-fecha_creacion")
        .first()
    )

    # ----------------------------------
    # Postulaciones del usuario
    # ----------------------------------
    postulaciones = (
        Postulacion.objects
        .filter(user=user)
        .select_related("convocatoria")
        .order_by("-fecha_envio")
    )

    return render(
        request,
        "usuarios/panel.html",
        {
            "persona_humana": persona_humana,
            "persona_juridica": persona_juridica,
            "exencion": exencion,
            "postulaciones": postulaciones,
        },
    )


# ============================================================
# PANEL DE JURADO
# ============================================================

@login_required(login_url="/usuarios/login/")
def panel_jurado(request):
    user = request.user
    print(">>> ENTRÓ A panel_jurado (usuarios) <<<")

    # Seguridad
    if not user.groups.filter(name="jurado").exists():
        return redirect("usuarios:panel_usuario")

    # Convocatorias asignadas
    convocatorias_asignadas = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=user)
        .values_list("convocatoria_id", flat=True)
    )

    print("DEBUG jurado:", user.username)
    print("DEBUG convocatorias_asignadas:", list(convocatorias_asignadas))

    postulaciones = (
        Postulacion.objects
        .filter(
            estado="evaluacion_jurado",
            convocatoria_id__in=convocatorias_asignadas
        )
        .select_related("convocatoria", "user")
        .order_by("-fecha_envio")
    )

    print("DEBUG postulaciones:", postulaciones.count())

    return render(
        request,
        "usuarios/panel_jurado.html",
        {
            "postulaciones": postulaciones,
        }
    )

