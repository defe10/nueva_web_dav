from django import forms
from datetime import date
from .models import PersonaHumana, PersonaJuridica


# ============================================================
# PERSONA HUMANA
# ============================================================

class PersonaHumanaForm(forms.ModelForm):

    class Meta:
        model = PersonaHumana
        fields = [
            # Datos personales
            "nombre_completo",
            "cuil_cuit",
            "fecha_nacimiento",
            "edad",
            "genero",
            "lugar_residencia",
            "otro_lugar_residencia",
            "nivel_educativo",
            "domicilio_real",
            "codigo_postal_real",
            "telefono",
            "email",

            # Datos fiscales
            "situacion_iva",
            "actividad_dgr",
            "domicilio_fiscal",
            "codigo_postal_fiscal",
            "localidad_fiscal",

            # Datos profesionales
            "area_desempeno_1",
            "area_desempeno_2",
            "area_cultural",
            "link_1",
            "link_2",
            "link_3",
        ]

        widgets = {
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "edad": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "lugar_residencia": forms.Select(attrs={"class": "form-select"}),
            "otro_lugar_residencia": forms.TextInput(attrs={"class": "form-control"}),
            "nivel_educativo": forms.Select(attrs={"class": "form-select"}),
            "domicilio_real": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_real": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),

            "situacion_iva": forms.Select(attrs={"class": "form-select"}),
            "actividad_dgr": forms.Select(attrs={"class": "form-select"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "localidad_fiscal": forms.Select(attrs={"class": "form-select"}),

            "area_desempeno_1": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_2": forms.Select(attrs={"class": "form-select"}),
            "area_cultural": forms.Select(attrs={"class": "form-select"}),
            "link_1": forms.TextInput(attrs={"class": "form-control"}),
            "link_2": forms.TextInput(attrs={"class": "form-control"}),
            "link_3": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validación: otro lugar de residencia
        if (
            cleaned_data.get("lugar_residencia") == "otro"
            and not cleaned_data.get("otro_lugar_residencia")
        ):
            self.add_error(
                "otro_lugar_residencia",
                "Debe especificar el lugar de residencia."
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Calcular edad SIEMPRE en backend
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


# ============================================================
# PERSONA JURÍDICA
# ============================================================

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
            "antiguedad",
            "telefono",
            "email",

            "situacion_iva",
            "actividad_dgr",

            "area_desempeno_JJPP_1",
            "area_desempeno_JJPP_2",
            "link_1",
            "link_2",
            "link_3",
        ]

        widgets = {
            "tipo_persona_juridica": forms.Select(attrs={"class": "form-select"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_comercial": forms.TextInput(attrs={"class": "form-control"}),

            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "localidad_fiscal": forms.Select(attrs={"class": "form-select"}),
            "codigo_postal_fiscal": forms.TextInput(attrs={"class": "form-control"}),

            "fecha_constitucion": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "antiguedad": forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),

            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),

            "situacion_iva": forms.Select(attrs={"class": "form-select"}),
            "actividad_dgr": forms.Select(attrs={"class": "form-select"}),

            "area_desempeno_JJPP_1": forms.Select(attrs={"class": "form-select"}),
            "area_desempeno_JJPP_2": forms.Select(attrs={"class": "form-select"}),

            "link_1": forms.TextInput(attrs={"class": "form-control"}),
            "link_2": forms.TextInput(attrs={"class": "form-control"}),
            "link_3": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Calcular antigüedad SIEMPRE en backend
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