from django import forms
from django.forms import inlineformset_factory

from .models import (
    ConvocatoriaFormacion,
    MiembroFormador,
    ConfiguracionInscripcionFormacion,
    InscripcionFormacion,
    BLOQUE_PERSONAS_TITULO,
)


class ConvocatoriaFormacionForm(forms.ModelForm):
    class Meta:
        model = ConvocatoriaFormacion
        fields = [
            "titulo",
            "tipo_formacion",
            "descripcion_corta",
            "descripcion_larga",
            "tematica_genero",
            "requisitos",
            "beneficios",
            "bases_pdf",
            "imagen",
            "url_curso",
            "url_destino",
            "fecha_inicio",
            "fecha_fin",
            "bloque_personas",
            "orden",
        ]
        widgets = {
            "titulo":            forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "tipo_formacion":    forms.Select(attrs={"class": "form-select"}),
            "descripcion_corta": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "descripcion_larga": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "tematica_genero":   forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "requisitos":        forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "beneficios":        forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "url_curso":         forms.URLInput(attrs={"class": "form-control"}),
            "url_destino":       forms.TextInput(attrs={"class": "form-control"}),
            "fecha_inicio":      forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin":         forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "bloque_personas":   forms.Select(attrs={"class": "form-select"}),
            "orden":             forms.NumberInput(attrs={"class": "form-control"}),
        }


class MiembroFormadorForm(forms.ModelForm):
    class Meta:
        model = MiembroFormador
        fields = ["nombre", "bio", "foto", "orden"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo"}),
            "bio":    forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Breve descripción (opcional)"}),
            "foto":   forms.ClearableFileInput(attrs={"class": "form-control"}),
            "orden":  forms.NumberInput(attrs={"class": "form-control", "style": "width:80px"}),
        }


MiembroFormadorFormSet = inlineformset_factory(
    ConvocatoriaFormacion,
    MiembroFormador,
    form=MiembroFormadorForm,
    extra=0,
    can_delete=True,
)


class ConfiguracionInscripcionFormacionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionInscripcionFormacion
        fields = [
            "mostrar_nombre_apellido",
            "mostrar_dni",
            "mostrar_genero",
            "mostrar_edad",
            "mostrar_telefono",
            "mostrar_email",
            "mostrar_documentacion",
        ]
        widgets = {
            f: forms.CheckboxInput(attrs={"class": "form-check-input"})
            for f in fields
        }


class InscripcionFormacionForm(forms.ModelForm):
    declaracion_jurada = forms.BooleanField(
        required=True,
        label="Declaro bajo juramento que la información presentada es verdadera.",
        error_messages={"required": "Debés aceptar la declaración jurada para continuar."},
    )

    class Meta:
        model = InscripcionFormacion
        fields = [
            "nombre",
            "apellido",
            "dni",
            "genero",
            "edad",
            "email",
            "telefono",
            "localidad",
            "otra_localidad",
            "vinculo_sector",
            "documentacion",
            "declaracion_jurada",
        ]
        widgets = {
            "nombre":             forms.TextInput(attrs={"class": "form-control"}),
            "apellido":           forms.TextInput(attrs={"class": "form-control"}),
            "dni":                forms.TextInput(attrs={"class": "form-control"}),
            "genero":             forms.Select(attrs={"class": "form-select"}),
            "edad":               forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 120}),
            "email":              forms.EmailInput(attrs={"class": "form-control"}),
            "telefono":           forms.TextInput(attrs={"class": "form-control"}),
            "localidad":          forms.Select(attrs={"class": "form-select"}),
            "otra_localidad":     forms.TextInput(attrs={"class": "form-control"}),
            "vinculo_sector":     forms.Select(attrs={"class": "form-select"}),
            "declaracion_jurada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.persona_humana   = kwargs.pop("persona_humana", None)
        self.persona_juridica = kwargs.pop("persona_juridica", None)
        config = kwargs.pop("config", None)
        super().__init__(*args, **kwargs)

        self.fields["otra_localidad"].required = False

        tiene_registro = bool(self.persona_humana or self.persona_juridica)
        identidad = ["nombre", "apellido", "dni", "email", "telefono", "localidad", "otra_localidad"]

        if tiene_registro:
            for f in identidad:
                if f in self.fields:
                    self.fields[f].required = False
                    self.fields[f].widget = forms.HiddenInput()
        else:
            self.fields["localidad"].required = True

        extras = {
            "genero":        config.mostrar_genero        if config else False,
            "edad":          config.mostrar_edad          if config else False,
            "documentacion": config.mostrar_documentacion if config else False,
        }
        if not tiene_registro and config:
            if not config.mostrar_nombre_apellido:
                for f in ["nombre", "apellido"]:
                    self.fields[f].required = False
                    self.fields[f].widget = forms.HiddenInput()
            if not config.mostrar_dni:
                self.fields["dni"].required = False
                self.fields["dni"].widget = forms.HiddenInput()
            if not config.mostrar_email:
                self.fields["email"].required = False
                self.fields["email"].widget = forms.HiddenInput()
            if not config.mostrar_telefono:
                self.fields["telefono"].required = False
                self.fields["telefono"].widget = forms.HiddenInput()

        for field_name, mostrar in extras.items():
            if not mostrar and field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()

        if self.persona_humana or self.persona_juridica:
            persona = self.persona_humana or self.persona_juridica

            def pick(*vals):
                for v in vals:
                    if v not in [None, ""]:
                        return v
                return ""

            cleaned["nombre"]    = pick(cleaned.get("nombre"),    getattr(persona, "nombre", None), getattr(persona, "nombre_completo", None))
            cleaned["apellido"]  = pick(cleaned.get("apellido"),  getattr(persona, "apellido", None))
            cleaned["dni"]       = pick(cleaned.get("dni"),       getattr(persona, "dni", None))
            cleaned["email"]     = pick(cleaned.get("email"),     getattr(persona, "email", None))
            cleaned["telefono"]  = pick(cleaned.get("telefono"),  getattr(persona, "telefono", None))
            cleaned["localidad"] = pick(cleaned.get("localidad"), getattr(persona, "localidad", None), getattr(persona, "lugar_residencia", None))
            return cleaned

        loc  = cleaned.get("localidad")
        otra = (cleaned.get("otra_localidad") or "").strip()
        if str(loc).lower() == "otro" and not otra:
            self.add_error("otra_localidad", 'Indicá la localidad si elegiste "Otro".')
        return cleaned
