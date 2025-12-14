from django import forms
from django.utils.text import slugify
from .models import Postulacion, Convocatoria, Jurado


# convocatorias/forms.py
from django import forms
from .models import Postulacion

class PostulacionForm(forms.ModelForm):
    class Meta:
        model = Postulacion
        fields = [
            "nombre_proyecto",
            "tipo_proyecto",
            "genero",
            # "duracion_minutos",
            "declaracion_jurada",
        ]
        widgets = {
            "nombre_proyecto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_proyecto": forms.Select(attrs={"class": "form-select"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            # "duracion_minutos": forms.NumberInput(attrs={"class": "form-control"}),
            "declaracion_jurada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }



class ConvocatoriaForm(forms.ModelForm):
    class Meta:
        model = Convocatoria
        fields = [
            # DATOS PRINCIPALES
            "titulo",
            "descripcion_corta",
            "descripcion_larga",

            # CLASIFICACIÓN
            "linea",            # ← AGREGADO
            "categoria",

            # DETALLES
            "tematica_genero",
            "requisitos",
            "beneficios",

            # ARCHIVOS
            "bases_pdf",
            "imagen",
            "url_curso",

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

            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),

            "bloque_personas": forms.Select(attrs={"class": "form-select"}),
            "jurado1_nombre":forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "jurado2_nombre":forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "jurado3_nombre":forms.Textarea(attrs={"rows": 1, "class": "form-control"}),
            "jurado1_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado2_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado3_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.slug = slugify(obj.titulo)

        if commit:
            obj.save()
            self.save_m2m()

        return obj

