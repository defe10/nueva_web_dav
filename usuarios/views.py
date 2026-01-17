from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.db.models import Q


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
from convocatorias.models import (
    Postulacion,
    AsignacionJuradoConvocatoria,
    InscripcionFormacion,
    Rendicion,
    DocumentoPostulacion,  # ✅ IMPORT REAL
)


# ============================================================
# LOGOUT
# ============================================================
def logout_usuario(request):
    logout(request)
    return redirect("/")


# ============================================================
# REGISTRO DE USUARIO
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

            html_message = render_to_string("usuarios/email_confirmacion.html", context)

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

            messages.success(request, "Tu cuenta fue creada. Revisá tu correo para activarla.")
            return redirect("usuarios:login")

    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})


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
                    messages.error(request, "Tu cuenta aún no está activada. Revisá tu correo.")
                    return redirect("usuarios:login")

                login(request, user)

                # Si hay next, respetarlo... pero no mandes a jurado al panel usuario
                if next_url and next_url.startswith("/"):
                    es_jurado = user.groups.filter(name__iexact="jurado").exists()

                    # Normalizá barras finales
                    next_clean = next_url.rstrip("/")

                    # Si jurado intenta ir a /usuarios/panel -> lo mandamos a su panel
                    if es_jurado and next_clean == "/usuarios/panel":
                        return redirect("usuarios:panel_jurado")

                    return redirect(next_url)

                return redirect("usuarios:redireccion_post_login")

        else:
            form = LoginForm(request)

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
        messages.success(request, "Tu cuenta fue activada. Ya podés iniciar sesión.")
        return redirect("usuarios:login")

    messages.error(request, "El enlace de activación no es válido o ya expiró.")
    return redirect("usuarios:login")


# ============================================================
# REDIRECCIÓN POST LOGIN
# ============================================================
@login_required(login_url="/usuarios/login/")
def redireccion_post_login(request):
    user = request.user

    if user.groups.filter(name__iexact="jurado").exists():
        return redirect("usuarios:panel_jurado")

    return redirect("usuarios:panel_usuario")


# ============================================================
# PANEL DE USUARIO
# ============================================================
@login_required(login_url="/usuarios/login/")
def panel_usuario(request):
    user = request.user

    persona_humana = PersonaHumana.objects.filter(user=user).first()
    persona_juridica = PersonaJuridica.objects.filter(user=user).first()

    exencion = (
        Exencion.objects
        .filter(user=user)
        .order_by("-fecha_creacion")
        .first()
    )

    exencion_observaciones_pendientes = []
    if exencion:
        exencion_observaciones_pendientes = list(
            exencion.observaciones
            .filter(subsanada=False)
            .order_by("-fecha_creacion")
        )

    postulaciones = (
        Postulacion.objects
        .filter(user=user)
        .select_related("convocatoria")
        .prefetch_related("observaciones")
        .order_by("-fecha_envio")
    )

    rendiciones = (
        Rendicion.objects
        .filter(
            user=user,
            postulacion__estado="seleccionado",
        )
        .select_related("postulacion", "postulacion__convocatoria")
        .order_by("-fecha_creacion")
    )

    inscripciones_formacion = (
        InscripcionFormacion.objects
        .filter(user=user)
        .select_related("convocatoria")
        .order_by("-fecha")
    )

    return render(
        request,
        "usuarios/panel.html",
        {
            "persona_humana": persona_humana,
            "persona_juridica": persona_juridica,
            "exencion": exencion,
            "exencion_observaciones_pendientes": exencion_observaciones_pendientes,
            "postulaciones": postulaciones,
            "rendiciones": rendiciones,
            "inscripciones_formacion": inscripciones_formacion,
        },
    )


# ============================================================
# PANEL DE JURADO
# ============================================================
@login_required(login_url="/usuarios/login/")
def panel_jurado(request):
    user = request.user

    if not user.groups.filter(name__iexact="jurado").exists():
        return redirect("usuarios:panel_usuario")

    convocatorias_asignadas = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=user)
        .values_list("convocatoria_id", flat=True)
    )

    postulaciones = (
        Postulacion.objects
        .filter(
            estado="evaluacion_jurado",
            convocatoria_id__in=convocatorias_asignadas
        )
        .select_related("convocatoria", "user")
        .order_by("-fecha_envio")
    )

    return render(
        request,
        "usuarios/panel_jurado.html",
        {"postulaciones": postulaciones},
    )


# ============================================================
# DOCUMENTACIÓN DEL PROYECTO (JURADO)
# ============================================================
@login_required(login_url="/usuarios/login/")
def jurado_ver_documentacion(request, postulacion_id):
    user = request.user

    if not user.groups.filter(name__iexact="jurado").exists():
        return redirect("usuarios:panel_usuario")

    convocatorias_asignadas = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=user)
        .values_list("convocatoria_id", flat=True)
    )

    postulacion = get_object_or_404(
        Postulacion.objects.select_related("convocatoria", "user"),
        id=postulacion_id,
        convocatoria_id__in=convocatorias_asignadas,
    )

    documentos = (
        DocumentoPostulacion.objects
        .filter(
            postulacion=postulacion,
            estado="ENVIADO",
        )
        .filter(
            Q(tipo="PROYECTO") |
            Q(tipo="SUBSANADO", subtipo_subsanado="PROYECTO")
        )
        .order_by("-fecha_subida")
    )



    return render(
        request,
        "usuarios/jurado_documentacion.html",
        {"postulacion": postulacion, "documentos": documentos},
    )

