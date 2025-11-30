from django import forms
from .models import PersonaHumana, PersonaJuridica, LUGARES_RESIDENCIA


class PersonaHumanaForm(forms.ModelForm):
    class Meta:
        model = PersonaHumana
        fields = [
            'nombre_completo',
            'cuil_cuit',
            'fecha_nacimiento',
            'edad',
            'lugar_residencia',
            'residencia_otro',
            'domicilio_real',
            'telefono_contacto',
            'correo_electronico',
            'genero',
            'nivel_educativo',
            'area_desempeno_1',
            'area_desempeno_2',
            'area_desempeno_3',
            'area_cultural_complementaria',
            'medios_experiencia',
            'links',
        ]

    def clean(self):
        cleaned_data = super().clean()
        lugar = cleaned_data.get("lugar_residencia")
        residencia_otro = cleaned_data.get("residencia_otro")

        if lugar == 'OTRO' and not residencia_otro:
            self.add_error('residencia_otro', "Debe especificar el lugar de residencia.")

        return cleaned_data


class PersonaJuridicaForm(forms.ModelForm):
    class Meta:
        model = PersonaJuridica
        fields = [
            'razon_social',
            'nombre_comercial',
            'tipo_persona_juridica',
            'area_desempeno_1',
            'area_desempeno_2',
        ]
