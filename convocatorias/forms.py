from django import forms
from django.utils.text import slugify

from .models import (
    Postulacion,
    Convocatoria,
    Jurado,  # lo dejo porque lo importabas (aunque no lo uses acá)
    DocumentoPostulacion,
    InscripcionFormacion,  # ✅ NUEVO
)


# ============================================================
# POSTULACIÓN (IDEA)
# ============================================================
class PostulacionForm(forms.ModelForm):
    # ✅ OBLIGATORIO (backend): si no tilda, el form es inválido
    declaracion_jurada = forms.BooleanField(
        required=True,
        label="Declaro bajo juramento que la información presentada es verdadera.",
        error_messages={"required": "Debés aceptar la declaración jurada para continuar."},
    )

    class Meta:
        model = Postulacion
        fields = [
            "nombre_proyecto",
            "tipo_proyecto",
            "genero",
            "declaracion_jurada",
        ]
        widgets = {
            "nombre_proyecto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_proyecto": forms.Select(attrs={"class": "form-select"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "declaracion_jurada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ============================================================
# FORMULARIO CREAR/EDITAR CONVOCATORIA (ADMIN PÚBLICO)
# ============================================================
class ConvocatoriaForm(forms.ModelForm):
    class Meta:
        model = Convocatoria
        fields = [
            # DATOS PRINCIPALES
            "titulo",
            "descripcion_corta",
            "descripcion_larga",

            # CLASIFICACIÓN
            "linea",
            "categoria",

            # DETALLES
            "tematica_genero",
            "requisitos",
            "beneficios",

            # ARCHIVOS / LINKS
            "bases_pdf",
            "imagen",
            "url_curso",
            "url_destino",  # ✅ NUEVO (ya está en el modelo)

            # FECHAS
            "fecha_inicio",
            "fecha_fin",

            # PERSONAS INVITADAS
            "bloque_personas",
            "jurado1_nombre",
            "jurado1_foto",
            "jurado1_bio",
            "jurado2_nombre",
            "jurado2_foto",
            "jurado2_bio",
            "jurado3_nombre",
            "jurado3_foto",
            "jurado3_bio",

            # ORDEN
            "orden",
        ]

        widgets = {
            "linea": forms.Select(attrs={"class": "form-select"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),

            "orden": forms.NumberInput(attrs={"class": "form-control"}),
            "titulo": forms.Textarea(attrs={"rows": 1, "class": "form-control"}),

            "descripcion_corta": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "descripcion_larga": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),

            "tematica_genero": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "requisitos": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "beneficios": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),

            "url_curso": forms.URLInput(attrs={"class": "form-control"}),
            "url_destino": forms.TextInput(attrs={"class": "form-control"}),

            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "bloque_personas": forms.Select(attrs={"class": "form-select"}),

            "jurado1_nombre": forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "jurado2_nombre": forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "jurado3_nombre": forms.Textarea(attrs={"rows": 1, "class": "form-control"}),

            "jurado1_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado2_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado3_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    # ⚠️ IMPORTANTE:
    # No sobrescribimos save() para slug.
    # Tu modelo ya crea un slug único en Convocatoria.save().
    # Si lo pisás acá con slugify(titulo), podés duplicar y romper unique=True.


# ============================================================
# SUBSANACIÓN (archivo único)
# ============================================================
class DocumentoSubsanadoForm(forms.ModelForm):
    class Meta:
        model = DocumentoPostulacion
        fields = ["archivo"]
        widgets = {
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control"})
        }


# ============================================================
# FORMACIÓN — INSCRIPCIÓN (sin obligar Registro Audiovisual)
# ============================================================
class InscripcionFormacionForm(forms.ModelForm):
    # ✅ OBLIGATORIO (backend) también acá
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
            "email",
            "telefono",
            "localidad",
            "otra_localidad",
            "vinculo_sector",
            "declaracion_jurada",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),

            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),

            "localidad": forms.Select(attrs={"class": "form-select"}),
            "otra_localidad": forms.TextInput(attrs={"class": "form-control"}),

            "vinculo_sector": forms.Select(attrs={"class": "form-select"}),

            "declaracion_jurada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.persona_humana = kwargs.pop("persona_humana", None)
        self.persona_juridica = kwargs.pop("persona_juridica", None)
        super().__init__(*args, **kwargs)

        # por defecto, "otra_localidad" no es obligatoria
        self.fields["otra_localidad"].required = False

        # Si hay registro: ocultar y no exigir datos base + localidad
        if self.persona_humana or self.persona_juridica:
            for f in ["nombre", "apellido", "dni", "email", "telefono", "localidad", "otra_localidad"]:
                if f in self.fields:
                    self.fields[f].required = False
                    self.fields[f].widget = forms.HiddenInput()
        else:
            # si NO hay registro, localidad sí es obligatoria
            if "localidad" in self.fields:
                self.fields["localidad"].required = True

    def clean(self):
        cleaned = super().clean()

        # Si hay registro: forzar datos desde registro (evita errores de "campo requerido")
        if self.persona_humana or self.persona_juridica:
            persona = self.persona_humana or self.persona_juridica

            def pick(*vals):
                for v in vals:
                    if v not in [None, ""]:
                        return v
                return ""

            cleaned["nombre"] = pick(
                cleaned.get("nombre"),
                getattr(persona, "nombre", None),
                getattr(persona, "nombre_completo", None),
            )
            cleaned["apellido"] = pick(
                cleaned.get("apellido"),
                getattr(persona, "apellido", None),
            )
            cleaned["dni"] = pick(
                cleaned.get("dni"),
                getattr(persona, "dni", None),
            )
            cleaned["email"] = pick(
                cleaned.get("email"),
                getattr(persona, "email", None),
            )
            cleaned["telefono"] = pick(
                cleaned.get("telefono"),
                getattr(persona, "telefono", None),
            )
            cleaned["localidad"] = pick(
                cleaned.get("localidad"),
                getattr(persona, "localidad", None),
                getattr(persona, "lugar_residencia", None),
            )

            return cleaned

        # Si NO hay registro: validar "otro"
        loc = cleaned.get("localidad")
        otra = (cleaned.get("otra_localidad") or "").strip()
        if str(loc).lower() == "otro" and not otra:
            self.add_error("otra_localidad", "Indicá la localidad si elegiste “Otro”.")
        return cleaned
