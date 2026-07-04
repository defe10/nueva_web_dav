import os
from django.core.exceptions import ValidationError


def validar_documento_admitido(archivo):
    extensiones_admitidas = {".pdf", ".xls", ".xlsx", ".ods"}
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in extensiones_admitidas:
        raise ValidationError(
            "Formato no admitido. Solo se permiten: PDF (.pdf), Excel (.xls, .xlsx) o planilla (.ods)."
        )


def validar_tamano_archivo(archivo):
    max_mb = 25
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo no puede superar los {max_mb} MB.")
