from django import template
import os

register = template.Library()

@register.filter
def nombre_original(value):
    if not value:
        return ""

    nombre = os.path.basename(str(value))
    base, ext = os.path.splitext(nombre)

    if "_" in base:
        base = base.rsplit("_", 1)[0]

    return f"{base}{ext}"
