from django import template

register = template.Library()

@register.filter
def rol_usuario(user):
    if not user.is_authenticated:
        return ""
    if user.groups.filter(name="admin").exists():
        return "Administrador"
    if user.groups.filter(name="jurado").exists():
        return "Jurado"
    return "Usuario"
