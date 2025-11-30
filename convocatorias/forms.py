from django import forms
from .models import PostulacionIDEA

class PostulacionIdeaForm(forms.ModelForm):
    declaracion_jurada = forms.BooleanField(required=True)

    class Meta:
        model = PostulacionIDEA
        fields = [
            'linea_fomento',
            'nombre_proyecto',
            'tipo_proyecto',
            'genero',
            'duracion_minutos',
            'declaracion_jurada',
        ]
