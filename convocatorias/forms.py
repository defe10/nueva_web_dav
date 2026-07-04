from django import forms
from django.forms import inlineformset_factory
from django.utils.text import slugify

from .models import (
    Postulacion,
    Convocatoria,
    ConfiguracionPostulacion,
    MiembroJurado,
    DocumentoPostulacion,
    DocumentoIntegrante,
    IntegrantePostulacion,
    CriterioEvaluacion,
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
            "url_destino",

            # FECHAS
            "fecha_inicio",
            "fecha_fin",

            # PERSONAS INVITADAS
            "bloque_personas",

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

            "url_destino": forms.TextInput(attrs={"class": "form-control"}),

            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "bloque_personas": forms.Select(attrs={"class": "form-select"}),
        }

    # ⚠️ IMPORTANTE:
    # No sobrescribimos save() para slug.
    # Tu modelo ya crea un slug único en Convocatoria.save().
    # Si lo pisás acá con slugify(titulo), podés duplicar y romper unique=True.


# ============================================================
# CONFIGURACIÓN DE POSTULACIÓN
# ============================================================
class ConfiguracionPostulacionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionPostulacion
        exclude = ["convocatoria"]
        widgets = {
            "tipo_postulante": forms.Select(attrs={"class": "form-select"}),
            **{f: forms.CheckboxInput(attrs={"class": "form-check-input"})
               for f in [
                   "requiere_productor_responsable",
                   "requiere_director", "director_puede_coincidir",
                   "requiere_guionista", "requiere_realizador", "requiere_cbu",
                   "mostrar_titulo", "mostrar_formato", "mostrar_genero",
                   "requiere_sinopsis", "requiere_link_pitch",
                   "mostrar_guion", "mostrar_dossier", "mostrar_material_adicional",
                   "mostrar_planilla_oficial", "mostrar_dnda",
                   "mostrar_autorizacion_derechos", "mostrar_nota_intencion",
                   "mostrar_carta_intencion", "mostrar_constancia_invitacion",
                   "mostrar_documentacion",
               ]}
        }


# ============================================================
# WIZARD — PASO 1: PRODUCTOR (solo CBU)
# ============================================================
class ProductorCBUForm(forms.ModelForm):
    class Meta:
        model = Postulacion
        fields = ["cbu"]
        widgets = {
            "cbu": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 0000000000000000000000",
                "maxlength": 30,
            })
        }

    def __init__(self, *args, requiere_cbu=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cbu"].required = requiere_cbu
        if not requiere_cbu:
            self.fields["cbu"].widget = forms.HiddenInput()


# ============================================================
# WIZARD — DOCUMENTO DE INTEGRANTE (DNI o ARCA)
# ============================================================
class DocumentoIntegranteForm(forms.ModelForm):
    class Meta:
        model = DocumentoIntegrante
        fields = ["tipo", "archivo"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ============================================================
# WIZARD — PASO 2/3/4: BUSCAR INTEGRANTE (director / guionista / realizador)
# ============================================================
class IntegranteSearchForm(forms.Form):
    nombre_busqueda = forms.CharField(
        label="Nombre completo",
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Escribí el nombre completo tal como figura en el registro",
            "autocomplete": "off",
        })
    )


# ============================================================
# WIZARD — PASO PROYECTO: datos del proyecto
# ============================================================
class ProyectoDataForm(forms.ModelForm):
    class Meta:
        model = Postulacion
        fields = [
            "nombre_proyecto",
            "tipo_proyecto",
            "genero",
            "sinopsis_corta",
            "link_pitch",
        ]
        widgets = {
            "nombre_proyecto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_proyecto":   forms.Select(attrs={"class": "form-select"}),
            "genero":          forms.Select(attrs={"class": "form-select"}),
            "sinopsis_corta":  forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "maxlength": 3000,
                "placeholder": "Máximo 3000 caracteres.",
            }),
            "link_pitch": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),
        }

    def __init__(self, *args, config=None, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)
        self.fields["sinopsis_corta"].required = bool(config and config.requiere_sinopsis)
        self.fields["link_pitch"].required = bool(config and config.requiere_link_pitch)

        if config and not config.requiere_sinopsis:
            self.fields["sinopsis_corta"].widget.attrs["placeholder"] = "Opcional"
        if config and not config.requiere_link_pitch:
            self.fields["link_pitch"].widget.attrs["placeholder"] = "Opcional"

    def clean(self):
        cleaned = super().clean()
        # nombre_proyecto, tipo_proyecto y genero son siempre obligatorios
        for campo, label in [
            ("nombre_proyecto", "Título del proyecto"),
            ("tipo_proyecto", "Tipo de proyecto"),
            ("genero", "Género"),
        ]:
            if not cleaned.get(campo):
                self.add_error(campo, "Este campo es obligatorio.")
        return cleaned

    def clean_sinopsis_corta(self):
        valor = self.cleaned_data.get("sinopsis_corta", "")
        if len(valor) > 3000:
            raise forms.ValidationError("La sinopsis no puede superar los 3000 caracteres.")
        return valor


# ============================================================
# WIZARD — PASO DOCUMENTACIÓN: subida de archivos del proyecto
# ============================================================
class DocumentoProyectoForm(forms.ModelForm):
    class Meta:
        model = DocumentoPostulacion
        fields = ["tipo", "archivo"]
        widgets = {
            "tipo":    forms.HiddenInput(),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ============================================================
# WIZARD — PASO CONFIRMACIÓN: declaración jurada
# ============================================================
class DeclaracionJuradaForm(forms.Form):
    declaracion_jurada = forms.BooleanField(
        required=True,
        label="Declaro bajo juramento que la información presentada es verdadera y acepto las bases y condiciones de la convocatoria.",
        error_messages={"required": "Debés aceptar la declaración jurada para enviar la postulación."},
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


# ============================================================
# MIEMBRO DEL JURADO
# ============================================================
class MiembroJuradoForm(forms.ModelForm):
    class Meta:
        model = MiembroJurado
        fields = ["nombre", "bio", "foto", "orden"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo"}),
            "bio":    forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Breve descripción (opcional)"}),
            "foto":   forms.ClearableFileInput(attrs={"class": "form-control"}),
            "orden":  forms.NumberInput(attrs={"class": "form-control", "style": "width:80px"}),
        }


MiembroJuradoFormSet = inlineformset_factory(
    Convocatoria,
    MiembroJurado,
    form=MiembroJuradoForm,
    extra=0,
    can_delete=True,
)


class CriterioEvaluacionForm(forms.ModelForm):
    class Meta:
        model = CriterioEvaluacion
        fields = ["nombre", "puntaje_maximo", "orden"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Originalidad"}),
            "puntaje_maximo": forms.NumberInput(attrs={"class": "form-control", "style": "width:90px", "min": 1}),
            "orden": forms.NumberInput(attrs={"class": "form-control", "style": "width:80px", "min": 0}),
        }


CriterioEvaluacionFormSet = inlineformset_factory(
    Convocatoria,
    CriterioEvaluacion,
    form=CriterioEvaluacionForm,
    extra=0,
    can_delete=True,
)


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


