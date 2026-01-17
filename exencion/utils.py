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

# exencion/utils.py
def _valor_valido(valor):
    """
    Considera incompleto si:
    - None / "" / espacios
    - "ninguna", "ninguno", "-", "no corresponde" (en cualquier mayúsc/minúsc)
    """
    if valor is None:
        return False

    v = str(valor).strip().lower()

    if v in ["", "ninguna", "ninguno", "-", "no corresponde", "n/a", "na"]:
        return False

    return True


def datos_fiscales_completos(persona):
    return all([
        _valor_valido(getattr(persona, "situacion_iva", None)),
        _valor_valido(getattr(persona, "actividad_dgr", None)),
        _valor_valido(getattr(persona, "domicilio_fiscal", None)),
        _valor_valido(getattr(persona, "codigo_postal_fiscal", None)),
        _valor_valido(getattr(persona, "localidad_fiscal", None)),
    ])
