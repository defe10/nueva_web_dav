import re
import unicodedata

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Nodo, Opcion, PalabraClave, ConfiguracionChatbot, ConsultaLog

_MAX_HISTORIAL = 50


def normalizar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def _get_nodo_inicio():
    return Nodo.objects.filter(es_inicio=True, activo=True).first()


def _entry_bot(nodo):
    return {"tipo": "bot", "texto": nodo.mensaje, "nodo_id": nodo.id}


def _nodo_desde_historial(historial):
    """Devuelve el nodo correspondiente a la última entrada bot del historial."""
    for entry in reversed(historial):
        if entry.get("tipo") == "bot":
            nodo_id = entry.get("nodo_id")
            if nodo_id:
                nodo = Nodo.objects.filter(id=nodo_id).first()
                if nodo:
                    return nodo
    return _get_nodo_inicio()


def inicio_chatbot(request):
    nodo = _get_nodo_inicio()
    historial = [_entry_bot(nodo)]
    request.session["chat_historial"] = historial

    contexto = {"nodo": nodo, "historial": historial}

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
        return JsonResponse({"widget_html": widget_html})

    return render(request, "chatbot/chat.html", contexto)


def ver_nodo(request, opcion_id):
    opcion = get_object_or_404(Opcion, id=opcion_id)
    nodo = opcion.nodo_destino

    historial = request.session.get("chat_historial", [])
    historial.append({"tipo": "usuario", "texto": opcion.texto})
    historial.append(_entry_bot(nodo))

    # Limitar tamaño del historial para no saturar la sesión
    if len(historial) > _MAX_HISTORIAL:
        historial = historial[-_MAX_HISTORIAL:]

    request.session["chat_historial"] = historial

    contexto = {"nodo": nodo, "historial": historial}

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
        return JsonResponse({"widget_html": widget_html})

    return render(request, "chatbot/chat.html", contexto)


def volver(request):
    historial = request.session.get("chat_historial", [])

    if len(historial) >= 2:
        historial = historial[:-2]

    request.session["chat_historial"] = historial

    if historial:
        nodo = _nodo_desde_historial(historial)
    else:
        nodo = _get_nodo_inicio()
        historial = [_entry_bot(nodo)]
        request.session["chat_historial"] = historial

    contexto = {"nodo": nodo, "historial": historial}

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
        return JsonResponse({"widget_html": widget_html})

    return render(request, "chatbot/chat.html", contexto)


def buscar_consulta(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    consulta = request.POST.get("consulta", "").strip()
    consulta_normalizada = normalizar_texto(consulta)

    historial = request.session.get("chat_historial", [])

    if consulta:
        historial.append({"tipo": "usuario", "texto": consulta})

    palabras_clave = PalabraClave.objects.filter(activo=True).select_related("nodo_destino")

    # B: word boundary — la keyword debe ser una palabra completa, no substring
    def _matchea(kw_normalizada, texto_normalizado):
        patron = r'\b' + re.escape(kw_normalizada) + r'\b'
        return bool(re.search(patron, texto_normalizado))

    coincidencias = [
        p for p in palabras_clave
        if p.texto and _matchea(normalizar_texto(p.texto), consulta_normalizada)
    ]

    keyword_matcheada = None
    if coincidencias:
        mejor = max(coincidencias, key=lambda p: (p.prioridad, len(normalizar_texto(p.texto))))
        keyword_matcheada = mejor.texto
        nodo = mejor.nodo_destino
        historial.append(_entry_bot(nodo))
    else:
        nodo = _get_nodo_inicio()
        config = ConfiguracionChatbot.get()
        msg_no_encontrado = (
            config.mensaje_no_encontrado if config
            else "No estoy seguro de haber entendido. Podés reformular la consulta o elegir una de las opciones disponibles."
        )
        historial.append({
            "tipo": "bot",
            "texto": msg_no_encontrado,
            "nodo_id": nodo.id if nodo else None,
        })

    # F: registrar consulta
    if consulta:
        ConsultaLog.objects.create(
            texto_consulta=consulta[:500],
            keyword_matcheada=keyword_matcheada,
            nodo_destino=nodo,
            encontrado=bool(coincidencias),
        )

    if len(historial) > _MAX_HISTORIAL:
        historial = historial[-_MAX_HISTORIAL:]

    request.session["chat_historial"] = historial

    contexto = {"nodo": nodo, "historial": historial}

    widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
    return JsonResponse({"widget_html": widget_html})


def widget_chatbot(request):
    historial = request.session.get("chat_historial")

    if not historial:
        nodo = _get_nodo_inicio()
        historial = [_entry_bot(nodo)]
        request.session["chat_historial"] = historial
    else:
        nodo = _nodo_desde_historial(historial)

    contexto = {"nodo": nodo, "historial": historial}

    return render(request, "chatbot/_widget_shell.html", contexto)