from django import forms
from django.utils.text import slugify
from .models import PostulacionIDEA, Convocatoria, Jurado


class PostulacionIdeaForm(forms.ModelForm):
    declaracion_jurada = forms.BooleanField(required=True)

    class Meta:
        model = PostulacionIDEA
        fields = [
            "linea_fomento",
            "nombre_proyecto",
            "tipo_proyecto",
            "genero",
            "duracion_minutos",
            "declaracion_jurada",
        ]


class ConvocatoriaForm(forms.ModelForm):
    class Meta:
        model = Convocatoria
        fields = [
            "titulo",
            "descripcion_corta",
            "descripcion_larga",

            "categoria",
            "tematica_genero",
            "requisitos",
            "beneficios",

            "bases_pdf",
            "imagen",

            "fecha_inicio",
            "fecha_fin",
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
          
            "orden",
        ]

        widgets = {
            "descripcion_corta": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "descripcion_larga": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "tematica_genero": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "requisitos": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "beneficios": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
            "bloque_personas": forms.Select(attrs={"class": "form-select"}),
            "jurado1_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado2_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "jurado3_bio": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
}
        


    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.slug = slugify(obj.titulo)

        if commit:
            obj.save()
            self.save_m2m()  # ← NECESARIO PARA MANYTOMANY
        return obj
