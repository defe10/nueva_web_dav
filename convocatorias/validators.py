# convocatorias/validators.py

from django.core.exceptions import ValidationError

def validar_pdf(archivo):
    if not archivo.name.lower().endswith(".pdf"):
        raise ValidationError("El archivo debe estar en formato PDF.")

def validar_tamano_archivo(archivo):
    max_mb = 5  # ajustable
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo no puede superar los {max_mb} MB.")
