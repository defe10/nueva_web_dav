# convocatorias/validators.py

import os
from django.core.exceptions import ValidationError


# ============================================================
#  VALIDACIONES DE ARCHIVOS
# ============================================================

def validar_pdf(archivo):
    """
    Valida que el archivo sea PDF (extensión .pdf).
    Útil para campos donde querés forzar SOLO PDF.
    """
    if not archivo.name.lower().endswith(".pdf"):
        raise ValidationError("El archivo debe estar en formato PDF.")


def validar_documento_admitido(archivo):
    """
    Valida formatos admitidos para convocatorias:
    - PDF: .pdf
    - Excel: .xls, .xlsx
    - Planillas tipo Google Sheets / LibreOffice: .ods
    """
    extensiones_admitidas = {".pdf", ".xls", ".xlsx", ".ods"}
    ext = os.path.splitext(archivo.name)[1].lower()

    if ext not in extensiones_admitidas:
        raise ValidationError(
            "Formato no admitido. Solo se permiten: PDF (.pdf), Excel (.xls, .xlsx) o planilla (.ods)."
        )


def validar_tamano_archivo(archivo):
    max_mb = 25  # ajustable
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo no puede superar los {max_mb} MB.")
