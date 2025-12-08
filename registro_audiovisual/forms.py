from django import forms
from datetime import date
from .models import PersonaHumana, PersonaJuridica
from .models import LUGARES_RESIDENCIA


class PersonaHumanaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lugar de residencia (select con "- Seleccionar -")
        if "lugar_residencia" in self.fields:
            self.fields["lugar_residencia"].choices = LUGARES_RESIDENCIA
            self.fields["lugar_residencia"].widget.attrs.update({"class": "form-select"})

        # Otro lugar
        if "otro_lugar_residencia" in self.fields:
            self.fields["otro_lugar_residencia"].widget.attrs.update(
                {"class": "form-control"}
            )

        # Edad solo lectura
        if "edad" in self.fields:
            self.fields["edad"].widget.attrs.update(
                {"readonly": "readonly", "class": "form-control"}
            )

        # Género como select con "- Seleccionar -"
        if "genero" in self.fields:
            self.fields["genero"].choices = [
                ("", "- Seleccionar -")
            ] + list(self.fields["genero"].choices)[1:]
            self.fields["genero"].widget.attrs.update({"class": "form-select"})

        # Nivel educativo: si quisieras que sea select, acá se ajusta.
        if "nivel_educativo" in self.fields:
            self.fields["nivel_educativo"].widget.attrs.update({"class": "form-control"})

        # Situación IVA y Actividad DGR (por ahora como texto, pero estilados)
        if "situacion_iva" in self.fields:
            self.fields["situacion_iva"].widget.attrs.update({"class": "form-control"})
        if "actividad_dgr" in self.fields:
            self.fields["actividad_dgr"].widget.attrs.update({"class": "form-control"})
        
        # Area desempeño 
        if "area_desempeno_1" in self.fields:
            self.fields["area_desempeno_1"].widget.attrs.update({"class": "form-control"})
      
        
        if "area_desempeno_2" in self.fields:
            self.fields["area_desempeno_2"].widget.attrs.update({"class": "form-control"})
      

        if "area_cultural" in self.fields:
            self.fields["area_cultural"].widget.attrs.update({"class": "form-control"})
     
     

    def clean(self):
        cleaned_data = super().clean()

        # Validación "otro" lugar
        lugar = cleaned_data.get("lugar_residencia")
        otro = cleaned_data.get("otro_lugar_residencia")

        if lugar == "otro" and not otro:
            self.add_error(
                "otro_lugar_residencia",
                "Debe especificar el lugar de residencia."
            )

        # Calcular edad automáticamente a partir de fecha_nacimiento
        fecha_nacimiento = cleaned_data.get("fecha_nacimiento")
        if fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
            )
            cleaned_data["edad"] = edad  # ModelForm usará este valor para el modelo

        return cleaned_data

    class Meta:
        model = PersonaHumana
        fields = [
            "nombre_completo",
            "cuil_cuit",
            "fecha_nacimiento",
            "edad",  # importante incluirlo para que se guarde
            "genero",
            "lugar_residencia",
            "otro_lugar_residencia",
            "nivel_educativo",
            "domicilio_real",
            "telefono",
            "email",
            "situacion_iva",
            "actividad_dgr",
            "domicilio_fiscal",
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
            "fecha_nacimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "domicilio_real": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "link_1": forms.TextInput(attrs={"class": "form-control"}),
            "link_2": forms.TextInput(attrs={"class": "form-control"}),
            "link_3": forms.TextInput(attrs={"class": "form-control"}),
        }

def clean_email(self):
    email = self.cleaned_data.get("email")

    if email and "@" not in email:
        raise forms.ValidationError("El correo electrónico debe contener '@'.")

    return email

class PersonaJuridicaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tipo de persona jurídica
        if "tipo_persona_juridica" in self.fields:
            self.fields["tipo_persona_juridica"].choices = [
                ("", "- Seleccionar -")
            ] + list(self.fields["tipo_persona_juridica"].choices)[1:]
            self.fields["tipo_persona_juridica"].widget.attrs.update(
                {"class": "form-select"}
            )

        # Lugar de residencia
        if "lugar_residencia" in self.fields:
            self.fields["lugar_residencia"].choices = LUGARES_RESIDENCIA
            self.fields["lugar_residencia"].widget.attrs.update({"class": "form-select"})
            

        # Antigüedad solo lectura (si querés que se calcule sola)
        if "antiguedad" in self.fields:
            self.fields["antiguedad"].widget.attrs.update(
                {"readonly": "readonly", "class": "form-control"}
            )

        # Situación IVA y Actividad DGR
        if "situacion_iva" in self.fields:
            self.fields["situacion_iva"].widget.attrs.update({"class": "form-control"})
        if "actividad_dgr" in self.fields:
            self.fields["actividad_dgr"].widget.attrs.update({"class": "form-control"})

        # Area desempeño 
        if "area_desempeno_JJPP_1" in self.fields:
            self.fields["area_desempeno_JJPP_1"].widget.attrs.update({"class": "form-control"})
       
        
        if "area_desempeno_JJPP_2" in self.fields:
            self.fields["area_desempeno_JJPP_2"].widget.attrs.update({"class": "form-control"})

        

    def clean(self):
        cleaned_data = super().clean()

        # Calcular antigüedad a partir de fecha_constitucion
        fecha_const = cleaned_data.get("fecha_constitucion")
        if fecha_const:
            hoy = date.today()
            antig = hoy.year - fecha_const.year - (
                (hoy.month, hoy.day) < (fecha_const.month, fecha_const.day)
            )
            cleaned_data["antiguedad"] = antig

        return cleaned_data

    class Meta:
        model = PersonaJuridica
        fields = [
            "tipo_persona_juridica",
            "cuil_cuit",
            "razon_social",
            "nombre_comercial",
            "domicilio_fiscal",
            "lugar_residencia",
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
            "fecha_constitucion": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "antiguedad": forms.NumberInput(attrs={"class": "form-control"}),
            "cuil_cuit": forms.TextInput(attrs={"class": "form-control"}),
            "razon_social": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_comercial": forms.TextInput(attrs={"class": "form-control"}),
            "domicilio_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "link_1": forms.TextInput(attrs={"class": "form-control"}),
            "link_2": forms.TextInput(attrs={"class": "form-control"}),
            "link_3": forms.TextInput(attrs={"class": "form-control"}),
        }
def clean_email(self):
    email = self.cleaned_data.get("email")

    if email and "@" not in email:
        raise forms.ValidationError("El correo electrónico debe contener '@'.")

    return email