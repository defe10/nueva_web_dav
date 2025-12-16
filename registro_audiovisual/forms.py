from django import forms
from datetime import date
from .models import PersonaHumana, PersonaJuridica, LUGARES_RESIDENCIA


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

            # Datos fiscales (opcionales en registro)
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
            # Datos personales
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "edad": forms.NumberInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "lugar_residencia": forms.Select(attrs={"class": "form-select"}),
            "otro_lugar_residencia": forms.TextInput(attrs={"class": "form-control"}),
            "nivel_educativo": forms.Select(attrs={"class": "form-select"}),
            "domicilio_real": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_real": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),

            # Datos fiscales
            "situacion_iva": forms.Select(attrs={"class": "form-select"}),
            "actividad_dgr": forms.Select(attrs={"class": "form-select"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_postal_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "localidad_fiscal": forms.Select(attrs={"class": "form-select"}),

            # Datos profesionales
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

        # Calcular edad automáticamente
        fecha_nac = cleaned_data.get("fecha_nacimiento")
        if fecha_nac:
            hoy = date.today()
            cleaned_data["edad"] = (
                hoy.year
                - fecha_nac.year
                - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            )

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and "@" not in email:
            raise forms.ValidationError("Ingrese un correo electrónico válido.")
        return email


# ============================================================
# PERSONA JURÍDICA
# ============================================================

class PersonaJuridicaForm(forms.ModelForm):

    class Meta:
        model = PersonaJuridica
        fields = [
            # Datos institucionales
            "tipo_persona_juridica",
            "cuil_cuit",
            "razon_social",
            "nombre_comercial",

            # Datos fiscales (OBLIGATORIOS)
            "domicilio_fiscal",
            "localidad_fiscal",
            "codigo_postal_fiscal",

            # Datos generales
            "fecha_constitucion",
            "antiguedad",
            "telefono",
            "email",

            # Datos fiscales complementarios
            "situacion_iva",
            "actividad_dgr",

            # Datos profesionales
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

            "fecha_constitucion": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "antiguedad": forms.NumberInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),

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

    def clean(self):
        cleaned_data = super().clean()

        # Calcular antigüedad automáticamente
        fecha_const = cleaned_data.get("fecha_constitucion")
        if fecha_const:
            hoy = date.today()
            cleaned_data["antiguedad"] = (
                hoy.year
                - fecha_const.year
                - ((hoy.month, hoy.day) < (fecha_const.month, fecha_const.day))
            )

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and "@" not in email:
            raise forms.ValidationError("Ingrese un correo electrónico válido.")
        return email
