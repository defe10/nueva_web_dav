from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.core.paginator import Paginator
from django.core import signing
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
import json

JURADO_GROUP = "jurado"
ESTADOS_JURADO = ["admitido", "evaluacion_jurado", "seleccionado", "no_seleccionado"]


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
    IntegrantePostulacion,
    Rendicion,
    DocumentoPostulacion,
    DocumentoIntegrante,
    CriterioEvaluacion,
    EvaluacionPostulacion,
    PuntajeCriterio,
)
from formacion.models import InscripcionFormacion


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
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
            )
            email.attach_alternative(html_message, "text/html")
            try:
                email.send()
                messages.success(request, "Tu cuenta fue creada. Revisá tu correo para activarla.")
            except Exception:
                messages.warning(
                    request,
                    "Tu cuenta fue creada pero no pudimos enviarte el email de activación. "
                    "Contactá al administrador para activar tu cuenta."
                )
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
                    es_jurado = user.groups.filter(name__iexact=JURADO_GROUP).exists()

                    # Normalizá barras finales
                    next_clean = next_url.rstrip("/")

                    # Si jurado intenta ir a /usuarios/panel -> lo mandamos a su panel
                    if es_jurado and next_clean in ("/usuarios/panel", "/usuarios/panel/"):
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
@ratelimit(key="ip", rate="10/h", block=True)
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

    if user.groups.filter(name__iexact=JURADO_GROUP).exists():
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

    postulaciones_qs = (
        Postulacion.objects
        .filter(user=user)
        .select_related("convocatoria")
        .prefetch_related("observaciones")
        .order_by("-fecha_creacion")
    )
    postulaciones_page = Paginator(postulaciones_qs, 10).get_page(request.GET.get("p_post"))


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
        .prefetch_related("observaciones")
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
            "postulaciones": postulaciones_page,
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

    if not user.groups.filter(name__iexact=JURADO_GROUP).exists():
        return redirect("usuarios:panel_usuario")

    asignaciones = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=user)
        .select_related("convocatoria")
        .order_by("convocatoria__titulo")
    )



    grupos = []
    for asig in asignaciones:
        postulaciones = (
            Postulacion.objects
            .filter(convocatoria=asig.convocatoria, estado__in=ESTADOS_JURADO)
            .select_related("convocatoria")
            .order_by("nombre_proyecto")
        )
        grupos.append({"convocatoria": asig.convocatoria, "postulaciones": postulaciones})

    return render(
        request,
        "usuarios/panel_jurado.html",
        {"grupos": grupos},
    )


# ============================================================
# DETALLE DE POSTULACIÓN (JURADO)
# ============================================================
@login_required(login_url="/usuarios/login/")
def jurado_ver_documentacion(request, postulacion_id):
    user = request.user

    if not user.groups.filter(name__iexact=JURADO_GROUP).exists():
        return redirect("usuarios:panel_usuario")

    convocatorias_asignadas = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=user)
        .values_list("convocatoria_id", flat=True)
    )

    postulacion = get_object_or_404(
        Postulacion.objects.select_related("convocatoria"),
        id=postulacion_id,
        convocatoria_id__in=convocatorias_asignadas,
        estado__in=ESTADOS_JURADO,
    )

    asignacion = AsignacionJuradoConvocatoria.objects.filter(
        jurado=user, convocatoria=postulacion.convocatoria
    ).first()
    doble_ciego = asignacion.doble_ciego if asignacion else False

    documentos_postulacion = (
        DocumentoPostulacion.objects
        .filter(postulacion=postulacion, estado="ENVIADO")
        .exclude(tipo="COMPROBANTE_CBU")
        .order_by("tipo", "-fecha_subida")
    )

    if not doble_ciego:
        cvs = {
            doc.integrante_id: doc.archivo.url
            for doc in DocumentoIntegrante.objects.filter(
                integrante__postulacion=postulacion,
                tipo="CV_BIOFILMOGRAFIA",
                estado="ENVIADO",
            )
        }
        integrantes_raw = (
            IntegrantePostulacion.objects
            .filter(postulacion=postulacion, rol__in=["DIRECTOR", "PRODUCTOR"])
            .select_related("persona_humana")
            .order_by("rol")
        )
        integrantes = [(i, cvs.get(i.id)) for i in integrantes_raw]
    else:
        integrantes = []

    return render(
        request,
        "usuarios/jurado_documentacion.html",
        {
            "postulacion":            postulacion,
            "integrantes":            integrantes,
            "doble_ciego":            doble_ciego,
            "documentos_postulacion": documentos_postulacion,
        },
    )


@login_required(login_url="/usuarios/login/")
def perfil_integrante(request, persona_id):
    if not request.user.groups.filter(name__iexact=JURADO_GROUP).exists():
        return redirect("usuarios:panel_usuario")

    persona = get_object_or_404(PersonaHumana, pk=persona_id)
    return render(request, "usuarios/perfil_integrante.html", {"persona": persona})



# ============================================================
# EVALUACIÓN DEL COMITÉ (JURADO)
# ============================================================

def _jurado_check(request):
    """Devuelve True si el usuario es jurado activo."""
    return request.user.is_authenticated and request.user.groups.filter(name__iexact=JURADO_GROUP).exists()


@login_required(login_url="/usuarios/login/")
def evaluacion_lista(request, convocatoria_id):
    """Lista de postulaciones a evaluar para una convocatoria."""
    from convocatorias.models import Convocatoria
    if not _jurado_check(request):
        return redirect("usuarios:panel_usuario")

    asignacion = get_object_or_404(
        AsignacionJuradoConvocatoria,
        jurado=request.user,
        convocatoria_id=convocatoria_id,
    )
    convocatoria = asignacion.convocatoria

    criterios = list(CriterioEvaluacion.objects.filter(convocatoria=convocatoria).order_by("orden"))
    total_criterios = len(criterios)
    if not criterios:
        messages.warning(request, "Esta convocatoria todavía no tiene criterios de evaluación cargados.")

    postulaciones = (
        Postulacion.objects
        .filter(convocatoria=convocatoria, estado__in=ESTADOS_JURADO)
        .prefetch_related("evaluacion__puntajes")
        .order_by("nombre_proyecto")
    )

    items = []
    for p in postulaciones:
        ev = getattr(p, "evaluacion", None)
        items.append({
            "postulacion": p,
            "evaluacion": ev,
            "puntaje_total": ev.puntaje_total if ev else None,
            "no_puntuar": ev.no_puntuar if ev else False,
            "completa": ev is not None and (ev.no_puntuar or len(ev.puntajes.all()) == total_criterios),
        })

    return render(request, "usuarios/evaluacion_lista.html", {
        "convocatoria": convocatoria,
        "items": items,
        "puntaje_maximo_total": sum(c.puntaje_maximo for c in criterios),
    })


@login_required(login_url="/usuarios/login/")
def evaluacion_postulacion(request, postulacion_id):
    """Formulario de evaluación de una postulación."""
    if not _jurado_check(request):
        return redirect("usuarios:panel_usuario")

    convocatorias_asignadas = (
        AsignacionJuradoConvocatoria.objects
        .filter(jurado=request.user)
        .values_list("convocatoria_id", flat=True)
    )

    postulacion = get_object_or_404(
        Postulacion.objects.select_related("convocatoria"),
        id=postulacion_id,
        convocatoria_id__in=convocatorias_asignadas,
        estado__in=ESTADOS_JURADO,
    )

    criterios = CriterioEvaluacion.objects.filter(convocatoria=postulacion.convocatoria)
    evaluacion, _ = EvaluacionPostulacion.objects.get_or_create(postulacion=postulacion)

    puntajes_existentes = {p.criterio_id: p for p in evaluacion.puntajes.select_related("criterio")}

    if request.method == "POST":
        data = request.POST
        no_puntuar = data.get("no_puntuar") == "on"
        fundamentacion = data.get("fundamentacion", "").strip()

        evaluacion.no_puntuar = no_puntuar
        evaluacion.fundamentacion = fundamentacion
        evaluacion.ultima_edicion_por = request.user
        evaluacion.save()

        if not no_puntuar:
            for criterio in criterios:
                raw = data.get(f"puntaje_{criterio.id}", "").strip()
                puntaje_val = int(raw) if raw.isdigit() else None
                if puntaje_val is not None:
                    puntaje_val = min(puntaje_val, criterio.puntaje_maximo)
                obj, _ = PuntajeCriterio.objects.get_or_create(
                    evaluacion=evaluacion, criterio=criterio
                )
                obj.puntaje = puntaje_val
                obj.save()
        else:
            evaluacion.puntajes.all().delete()

        messages.success(request, "Evaluación guardada correctamente.")
        return redirect("usuarios:evaluacion_lista", convocatoria_id=postulacion.convocatoria_id)

    items_criterios = []
    for c in criterios:
        pc = puntajes_existentes.get(c.id)
        items_criterios.append({
            "criterio": c,
            "puntaje": pc.puntaje if pc else None,
        })

    puntaje_maximo_total = sum(c["criterio"].puntaje_maximo for c in items_criterios)

    return render(request, "usuarios/evaluacion_postulacion.html", {
        "postulacion": postulacion,
        "evaluacion": evaluacion,
        "items_criterios": items_criterios,
        "puntaje_maximo_total": puntaje_maximo_total,
    })


# ============================================================
# REENVÍO DE EMAIL DE ACTIVACIÓN
# ============================================================
_SALT_CAMBIO_EMAIL = "cambio-email-v1"

@ratelimit(key="ip", rate="5/h", block=True)
def reenviar_activacion(request):
    if request.user.is_authenticated:
        return redirect("usuarios:panel_usuario")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        # Respuesta genérica siempre para no filtrar si el email existe
        msg = "Si existe una cuenta con ese correo pendiente de activación, te enviamos un nuevo enlace."

        try:
            usuario = User.objects.get(email__iexact=email, is_active=False)
            current_site = get_current_site(request)
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
                f"Hola {usuario.first_name or usuario.username},\n\n"
                f"Hacé clic en este enlace para activar tu cuenta:\n\n"
                f"https://{current_site.domain}/usuarios/activar/{uid}/{token}/"
            )
            email_msg = EmailMultiAlternatives(
                "Confirmá tu cuenta",
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
            )
            email_msg.attach_alternative(html_message, "text/html")
            try:
                email_msg.send()
            except Exception:
                pass
        except User.DoesNotExist:
            pass

        messages.success(request, msg)
        return redirect("usuarios:login")

    return render(request, "usuarios/reenviar_activacion.html")


# ============================================================
# CAMBIO DE EMAIL (con verificación)
# ============================================================
@login_required(login_url="/usuarios/login/")
@ratelimit(key="user", rate="5/h", block=True)
def cambiar_email(request):
    if request.method == "POST":
        nuevo_email = request.POST.get("nuevo_email", "").strip().lower()

        if not nuevo_email:
            messages.error(request, "Ingresá un correo válido.")
            return render(request, "usuarios/cambiar_email.html")

        if nuevo_email == request.user.email.lower():
            messages.error(request, "El nuevo correo es igual al actual.")
            return render(request, "usuarios/cambiar_email.html")

        if User.objects.filter(email__iexact=nuevo_email).exclude(pk=request.user.pk).exists():
            messages.error(request, "Ya existe una cuenta con ese correo.")
            return render(request, "usuarios/cambiar_email.html")

        # Token firmado con el nuevo email y el pk del usuario (expira en 24 h)
        token = signing.dumps(
            {"uid": request.user.pk, "nuevo_email": nuevo_email},
            salt=_SALT_CAMBIO_EMAIL,
        )

        current_site = get_current_site(request)
        confirmar_url = f"https://{current_site.domain}/usuarios/cambiar-email/confirmar/{token}/"
        context = {
            "user": request.user,
            "nuevo_email": nuevo_email,
            "confirmar_url": confirmar_url,
            "anio": timezone.now().year,
        }
        html_message = render_to_string("usuarios/email_cambio_email.html", context)
        text_message = (
            f"Hola {request.user.first_name or request.user.username},\n\n"
            f"Recibimos una solicitud para cambiar el correo de tu cuenta a {nuevo_email}.\n\n"
            f"Confirmá el cambio haciendo clic aquí:\n{confirmar_url}\n\n"
            f"Este enlace expira en 24 horas. Si no solicitaste este cambio, ignorá este mensaje."
        )
        email_obj = EmailMultiAlternatives(
            "Confirmá tu nuevo correo",
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [nuevo_email],
        )
        email_obj.attach_alternative(html_message, "text/html")
        try:
            email_obj.send()
            messages.success(
                request,
                f"Te enviamos un enlace de confirmación a {nuevo_email}. "
                "Revisá tu correo (y la carpeta de spam) y hacé clic para confirmar el cambio."
            )
        except Exception:
            messages.error(request, "No pudimos enviar el correo de confirmación. Intentá de nuevo más tarde.")

        return redirect("usuarios:panel_usuario")

    return render(request, "usuarios/cambiar_email.html", {"email_actual": request.user.email})


@login_required(login_url="/usuarios/login/")
def confirmar_cambio_email(request, token):
    try:
        data = signing.loads(token, salt=_SALT_CAMBIO_EMAIL, max_age=86400)  # 24 h
    except signing.SignatureExpired:
        messages.error(request, "El enlace de confirmación expiró. Solicitá un nuevo cambio de correo.")
        return redirect("usuarios:cambiar_email")
    except signing.BadSignature:
        messages.error(request, "El enlace de confirmación no es válido.")
        return redirect("usuarios:panel_usuario")

    if data.get("uid") != request.user.pk:
        messages.error(request, "Este enlace no corresponde a tu cuenta.")
        return redirect("usuarios:panel_usuario")

    nuevo_email = data.get("nuevo_email")
    if User.objects.filter(email__iexact=nuevo_email).exclude(pk=request.user.pk).exists():
        messages.error(request, "Ese correo ya está en uso por otra cuenta.")
        return redirect("usuarios:panel_usuario")

    request.user.email = nuevo_email
    request.user.username = nuevo_email
    request.user.save(update_fields=["email", "username"])

    messages.success(request, f"Tu correo fue actualizado a {nuevo_email}.")
    return redirect("usuarios:panel_usuario")
