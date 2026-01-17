from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    existing = field.field.widget.attrs.get("class", "")
    merged = f"{existing} {css}".strip() if existing else css
    return field.as_widget(attrs={"class": merged})


@register.filter(name="add_attr")
def add_attr(field, attr):
    """
    Uso esperado:
      {{ field|add_attr:"id:mi_id" }}
      {{ field|add_attr:"type:text" }}

    Soporta valores que tengan ":" dentro:
      {{ field|add_attr:"data-x:uno:dos:tres" }}

    Si el formato viene mal, NO rompe el template.
    """
    try:
        if not attr:
            return field

        if ":" not in attr:
            # formato inválido, devolvemos el field sin romper
            return field

        key, value = attr.split(":", 1)  # ✅ solo separa en el primer ":"
        key = (key or "").strip()
        value = (value or "").strip()

        if not key:
            return field

        return field.as_widget(attrs={key: value})
    except Exception:
        return field
