# exencion/utils.py
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
import os


def generar_pdf_exencion(exencion):

    base_static = os.path.join(settings.BASE_DIR, "static")

    logo_path = "file://" + os.path.join(
        base_static, "exencion/img/sec_cultura_color.png"
    )
    firma_path = "file://" + os.path.join(
        base_static, "exencion/img/firma_casoni.png"
    )

    css_path = os.path.join(
        base_static, "exencion/css/certificado.css"
    )

    html_string = render_to_string(
        "exencion/certificado_exencion.html",
        {
            "exencion": exencion,
            "logo_path": logo_path,
            "firma_path": firma_path,
        }
    )

    pdf = HTML(string=html_string).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    return pdf
