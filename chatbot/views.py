import unicodedata

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Nodo, Opcion, PalabraClave


def normalizar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def inicio_chatbot(request):
    nodo = Nodo.objects.get(es_inicio=True)

    historial = [
        {
            "tipo": "bot",
            "texto": nodo.mensaje
        }
    ]
    request.session["chat_historial"] = historial

    contexto = {
        "nodo": nodo,
        "historial": historial
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
        return JsonResponse({"widget_html": widget_html})

    return render(request, "chatbot/chat.html", contexto)


def ver_nodo(request, opcion_id):
    opcion = get_object_or_404(Opcion, id=opcion_id)
    nodo = opcion.nodo_destino

    historial = request.session.get("chat_historial", [])

    historial.append({
        "tipo": "usuario",
        "texto": opcion.texto
    })

    historial.append({
        "tipo": "bot",
        "texto": nodo.mensaje
    })

    request.session["chat_historial"] = historial

    contexto = {
        "nodo": nodo,
        "historial": historial
    }

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
        ultimo_mensaje = historial[-1]["texto"]
        nodo = Nodo.objects.filter(mensaje=ultimo_mensaje).first()
        if not nodo:
            nodo = Nodo.objects.get(es_inicio=True)
    else:
        nodo = Nodo.objects.get(es_inicio=True)
        historial = [{"tipo": "bot", "texto": nodo.mensaje}]
        request.session["chat_historial"] = historial

    contexto = {
        "nodo": nodo,
        "historial": historial
    }

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
        historial.append({
            "tipo": "usuario",
            "texto": consulta
        })

    coincidencias = []

    palabras_clave = PalabraClave.objects.filter(activo=True).select_related("nodo_destino")

    for palabra in palabras_clave:
        palabra_normalizada = normalizar_texto(palabra.texto)

        if palabra_normalizada and palabra_normalizada in consulta_normalizada:
            coincidencias.append(palabra)

    if coincidencias:
        mejor_coincidencia = max(
            coincidencias,
            key=lambda p: (p.prioridad, len(normalizar_texto(p.texto)))
        )
        nodo = mejor_coincidencia.nodo_destino

        historial.append({
            "tipo": "bot",
            "texto": nodo.mensaje
        })
    else:
        nodo = Nodo.objects.get(es_inicio=True)

        historial.append({
            "tipo": "bot",
            "texto": (
                "No estoy seguro de haber entendido. "
                "Podés reformular la consulta o elegir una de las opciones disponibles."
            )
        })

    request.session["chat_historial"] = historial

    contexto = {
        "nodo": nodo,
        "historial": historial
    }

    widget_html = render_to_string("chatbot/_widget.html", contexto, request=request)
    return JsonResponse({"widget_html": widget_html})


def widget_chatbot(request):
    nodo = Nodo.objects.get(es_inicio=True)

    historial = request.session.get("chat_historial")

    if not historial:
        historial = [
            {
                "tipo": "bot",
                "texto": nodo.mensaje
            }
        ]
        request.session["chat_historial"] = historial
    else:
        ultimo_mensaje = historial[-1]["texto"]
        nodo_encontrado = Nodo.objects.filter(mensaje=ultimo_mensaje).first()
        if nodo_encontrado:
            nodo = nodo_encontrado

    contexto = {
        "nodo": nodo,
        "historial": historial
    }

    return render(request, "chatbot/_widget_shell.html", contexto)