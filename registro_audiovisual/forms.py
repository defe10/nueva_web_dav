from datetime import date
from django import forms
from .models import PersonaHumana, PersonaJuridica


def agregar_opcion_seleccionar(form, campos):
    """
    Agrega ('', '- Seleccionar -') al inicio de los Select del formulario.
    Sirve para ChoiceField basados en CharField + choices.
    """
    for campo in campos:
        if campo in form.fields:
            choices_actuales = list(form.fields[campo].choices)
            choices_sin_vacio = [c for c in choices_actuales if c[0] != ""]
            form.fields[campo].choices = [("", "- Seleccionar -")] + choices_sin_vacio


class PersonaHumanaForm(forms.ModelForm):
    class Meta:
        model = PersonaHumana
        fields = [
            "nombre_completo",
            "cuil_cuit",
            "fecha_nacimiento",
            "genero",
            "lugar_residencia",
            "otro_lugar_residencia",
            "nivel_educativo",
            "domicilio_real",
            "codigo_postal_real",
            "telefono",
            "email",
            "situacion_iva",
            "actividad_dgr",
            "domicilio_fiscal",
            "codigo_postal_fiscal",
            "localidad_fiscal",
            "area_desempeno_1",
            "area_desempeno_2",
            "area_cultural",
            "portfolio_web",
            "canal_video",
            "instagram",
            "linkedin",
            "link_trabajo_destacado",
        ]

        widgets = {
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "lugar_residencia": forms.Select(attrs={"class": "form-select"}),
            "otro_lugar_residencia": forms.TextInput(attrs={"class": "form-control"}),
            "nivel_educativo": forms.Select(attrs={"class": "form-select"}),
            "domicilio_real": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_real": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "situacion_iva": forms.Select(attrs={"class": "form-select"}),
            "actividad_dgr": forms.Select(attrs={"class": "form-select"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "localidad_fiscal": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_1": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_2": forms.Select(attrs={"class": "form-select"}),
            "area_cultural": forms.Select(attrs={"class": "form-select"}),
            "portfolio_web": forms.URLInput(attrs={"class": "form-control"}),
            "canal_video": forms.URLInput(attrs={"class": "form-control"}),
            "instagram": forms.URLInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "link_trabajo_destacado": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agregar_opcion_seleccionar(
            self,
            [
                "genero",
                "lugar_residencia",
                "nivel_educativo",
                "situacion_iva",
                "actividad_dgr",
                "localidad_fiscal",
                "area_desempeno_1",
                "area_desempeno_2",
                "area_cultural",
            ]
        )

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("lugar_residencia") == "otro"
            and not cleaned_data.get("otro_lugar_residencia")
        ):
            self.add_error(
                "otro_lugar_residencia",
                "Debe especificar el lugar de residencia."
            )

        return cleaned_data

    def clean_lugar_residencia(self):
        valor = self.cleaned_data.get("lugar_residencia")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un lugar de residencia.")
        return valor

    def clean_genero(self):
        valor = self.cleaned_data.get("genero")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un género.")
        return valor

    def clean_nivel_educativo(self):
        valor = self.cleaned_data.get("nivel_educativo")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un nivel educativo.")
        return valor

    def clean_area_desempeno_1(self):
        valor = self.cleaned_data.get("area_desempeno_1")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un área de desempeño principal.")
        return valor

    def clean_area_cultural(self):
        valor = self.cleaned_data.get("area_cultural")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un área cultural complementaria.")
        return valor

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.fecha_nacimiento:
            hoy = date.today()
            instance.edad = (
                hoy.year
                - instance.fecha_nacimiento.year
                - ((hoy.month, hoy.day) < (instance.fecha_nacimiento.month, instance.fecha_nacimiento.day))
            )

        if commit:
            instance.save()

        return instance


class PersonaJuridicaForm(forms.ModelForm):
    class Meta:
        model = PersonaJuridica
        fields = [
            "tipo_persona_juridica",
            "cuil_cuit",
            "razon_social",
            "nombre_comercial",
            "domicilio_fiscal",
            "localidad_fiscal",
            "codigo_postal_fiscal",
            "fecha_constitucion",
            "telefono",
            "email",
            "situacion_iva",
            "actividad_dgr",
            "area_desempeno_JJPP_1",
            "area_desempeno_JJPP_2",
            "portfolio_web",
            "canal_video",
            "instagram",
            "linkedin",
            "link_trabajo_destacado",
        ]

        widgets = {
            "tipo_persona_juridica": forms.Select(attrs={"class": "form-select"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_comercial": forms.TextInput(attrs={"class": "form-control"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "localidad_fiscal": forms.Select(attrs={"class": "form-select"}),
            "codigo_postal_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_constitucion": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"}
            ),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "situacion_iva": forms.Select(attrs={"class": "form-select"}),
            "actividad_dgr": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_JJPP_1": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_JJPP_2": forms.Select(attrs={"class": "form-select"}),
            "portfolio_web": forms.URLInput(attrs={"class": "form-control"}),
            "canal_video": forms.URLInput(attrs={"class": "form-control"}),
            "instagram": forms.URLInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "link_trabajo_destacado": forms.URLInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agregar_opcion_seleccionar(
            self,
            [
                "tipo_persona_juridica",
                "localidad_fiscal",
                "situacion_iva",
                "actividad_dgr",
                "area_desempeno_JJPP_1",
                "area_desempeno_JJPP_2",
            ]
        )

    def clean_tipo_persona_juridica(self):
        valor = self.cleaned_data.get("tipo_persona_juridica")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un tipo de persona jurídica.")
        return valor

    def clean_localidad_fiscal(self):
        valor = self.cleaned_data.get("localidad_fiscal")
        if not valor:
            raise forms.ValidationError("Debe seleccionar una localidad fiscal.")
        return valor

    def clean_situacion_iva(self):
        valor = self.cleaned_data.get("situacion_iva")
        if not valor:
            raise forms.ValidationError("Debe seleccionar una situación frente al IVA.")
        return valor

    def clean_actividad_dgr(self):
        valor = self.cleaned_data.get("actividad_dgr")
        if not valor:
            raise forms.ValidationError("Debe seleccionar una actividad DGR.")
        return valor

    def clean_area_desempeno_JJPP_1(self):
        valor = self.cleaned_data.get("area_desempeno_JJPP_1")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un área de desempeño principal.")
        return valor

    def clean_area_desempeno_JJPP_2(self):
        valor = self.cleaned_data.get("area_desempeno_JJPP_2")
        if not valor:
            raise forms.ValidationError("Debe seleccionar un área de desempeño secundaria.")
        return valor

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.fecha_constitucion:
            hoy = date.today()
            instance.antiguedad = (
                hoy.year
                - instance.fecha_constitucion.year
                - ((hoy.month, hoy.day) < (instance.fecha_constitucion.month, instance.fecha_constitucion.day))
            )

        if commit:
            instance.save()

        return instance