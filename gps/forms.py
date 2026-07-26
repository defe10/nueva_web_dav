from django import forms
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy

from convocatorias.models import Postulacion

from .models import Obra, Hito, FichaTecnica, CreditoFichaTecnica, TituloAnterior


_TXT = {"class": "form-control"}
_SEL = {"class": "form-select"}


class RegistroVinculoMixin(forms.ModelForm):
    """Convierte campos de texto de nombres en autocompletados que, además
    del texto libre, pueden guardar un vínculo (GenericForeignKey) con el
    Registro Audiovisual. Qué campos, lo define CONCEPTOS en cada subclase.

    Cada concepto suma un campo oculto ``<campo>_ref`` con formato ``"ct:id"``
    que el JS completa al elegir una coincidencia y vacía si se edita el texto.
    """

    # (campo_texto, campo_content_type, campo_object_id, campo_oculto_ref)
    CONCEPTOS = [
        ("direccion", "direccion_content_type", "direccion_object_id", "direccion_ref"),
        ("produccion", "produccion_content_type", "produccion_object_id", "produccion_ref"),
    ]

    class Media:
        css = {"all": ("gps/registro_autocomplete.css",)}
        js = ("gps/registro_autocomplete.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = str(reverse_lazy("gps:registro_buscar"))
        for text_f, ct_f, id_f, ref_f in self.CONCEPTOS:
            self.fields[ref_f] = forms.CharField(required=False, widget=forms.HiddenInput())
            # Estado inicial del vínculo, si la obra ya tenía uno.
            inst = getattr(self, "instance", None)
            if inst is not None and getattr(inst, id_f) and getattr(inst, ct_f + "_id"):
                self.fields[ref_f].initial = f"{getattr(inst, ct_f + '_id')}:{getattr(inst, id_f)}"
            # El input de texto pasa a ser autocompletado.
            widget = self.fields[text_f].widget
            widget.attrs.update({
                "data-registro-autocomplete": "true",
                "data-registro-url": url,
                "autocomplete": "off",
            })

    def clean(self):
        cleaned = super().clean()
        for text_f, ct_f, id_f, ref_f in self.CONCEPTOS:
            ref = (cleaned.get(ref_f) or "").strip()
            if not ref:
                continue
            try:
                ct_id, obj_id = (int(x) for x in ref.split(":"))
            except (ValueError, TypeError):
                self.add_error(text_f, "Vínculo con el registro inválido.")
                continue
            ct = ContentType.objects.filter(
                pk=ct_id, app_label="registro_audiovisual",
                model__in=("personahumana", "personajuridica"),
            ).first()
            if not ct or not ct.get_all_objects_for_this_type(pk=obj_id).exists():
                self.add_error(text_f, "El registro seleccionado ya no existe.")
                cleaned[ref_f] = ""
        return cleaned

    def save(self, commit=True):
        obra = super().save(commit=False)
        for text_f, ct_f, id_f, ref_f in self.CONCEPTOS:
            ref = (self.cleaned_data.get(ref_f) or "").strip()
            if ref:
                ct_id, obj_id = (int(x) for x in ref.split(":"))
                setattr(obra, ct_f + "_id", ct_id)
                setattr(obra, id_f, obj_id)
            else:
                setattr(obra, ct_f + "_id", None)
                setattr(obra, id_f, None)
        if commit:
            obra.save()
            self._save_m2m()
        return obra


class PostulacionesField(forms.ModelMultipleChoiceField):
    """Postulaciones a elegir, nombradas por convocatoria + proyecto.

    El __str__ de Postulacion incluye el username, que no aporta nada cuando el
    usuario está eligiendo entre sus propias postulaciones.
    """

    def label_from_instance(self, postulacion):
        proyecto = postulacion.nombre_proyecto or "(sin título)"
        return f"{postulacion.convocatoria.titulo} — {proyecto}"


class ObraForm(RegistroVinculoMixin):

    # Vínculo con el recorrido dentro de la plataforma. El queryset se arma en
    # __init__ con las postulaciones del titular: nadie puede colgarse de la
    # postulación de otro.
    postulaciones = PostulacionesField(
        label="Postulaciones de esta obra",
        queryset=Postulacion.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Marcá las convocatorias a las que presentaste esta obra.",
    )

    # Los títulos anteriores se archivan solos al renombrar la obra (ver
    # Obra.save). Estos dos campos son para los que la plataforma no vio: el
    # título de desarrollo de una obra vieja, o una fila cargada por error.
    titulo_anterior_nuevo = forms.CharField(
        label="Agregar un título anterior",
        max_length=255,
        required=False,
        help_text="Si la obra circuló con otro nombre —por ejemplo su título de "
                  "desarrollo—, anotalo acá para poder reconocerla.",
        widget=forms.TextInput(attrs=_TXT),
    )
    titulos_anteriores_eliminar = forms.ModelMultipleChoiceField(
        label="Quitar títulos anteriores",
        queryset=TituloAnterior.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Obra
        # `seguimiento` y `verificado` no van: son control interno de la
        # Secretaría y se manejan desde el /admin.
        fields = [
            "titulo", "formato", "genero",
            "anio_inicio", "anio_finalizacion", "duracion",
            "direccion", "produccion", "sinopsis",
            "portada", "enlace",
            "estado_produccion", "postulaciones",
        ]
        widgets = {
            "titulo":            forms.TextInput(attrs=_TXT),
            "formato":           forms.Select(attrs=_SEL),
            "genero":            forms.Select(attrs=_SEL),
            "anio_inicio":       forms.NumberInput(attrs=_TXT),
            "anio_finalizacion": forms.NumberInput(attrs=_TXT),
            "duracion":          forms.NumberInput(attrs={**_TXT, "min": 0}),
            "direccion":         forms.TextInput(attrs=_TXT),
            "produccion":        forms.TextInput(attrs=_TXT),
            "sinopsis":          forms.Textarea(attrs={**_TXT, "rows": 4}),
            "portada":           forms.ClearableFileInput(attrs={"class": "form-control"}),
            "enlace":            forms.URLInput(attrs=_TXT),
            "estado_produccion": forms.Select(attrs=_SEL),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos obligatorios en el formulario del titular. `titulo` ya lo es
        # a nivel de modelo; `anio_inicio` se exige solo acá.
        self.fields["titulo"].required = True
        self.fields["anio_inicio"].required = True
        if self.instance.pk:
            self.fields["titulos_anteriores_eliminar"].queryset = (
                self.instance.titulos_anteriores.all()
            )
        self.fields["postulaciones"].queryset = self._postulaciones_elegibles(user)

    def _postulaciones_elegibles(self, user):
        """Postulaciones del titular de la obra, más las ya vinculadas.

        Se toma el titular de la obra y no quien está editando, porque el staff
        también puede abrir este formulario. Las ya vinculadas se suman aparte
        para no descolgar una coproducción que cargó la Secretaría.
        """
        titular = self.instance.owner if self.instance.pk else user
        elegibles = Postulacion.objects.none()
        if titular is not None:
            elegibles = Postulacion.objects.filter(user=titular).exclude(estado="borrador")
        if self.instance.pk:
            elegibles = elegibles | self.instance.postulaciones.all()
        return elegibles.select_related("convocatoria").distinct()

    def clean(self):
        cleaned = super().clean()
        # "Año de finalización" solo se muestra —y se exige— si el estado es
        # "Finalizada".
        if cleaned.get("estado_produccion") == "finalizada" and not cleaned.get("anio_finalizacion"):
            self.add_error(
                "anio_finalizacion",
                "Indicá el año de finalización cuando la obra está finalizada.",
            )
        return cleaned

    def save(self, commit=True):
        obra = super().save(commit=commit)
        if commit:
            for titulo in self.cleaned_data.get("titulos_anteriores_eliminar", []):
                titulo.delete()
            nuevo = (self.cleaned_data.get("titulo_anterior_nuevo") or "").strip()
            # El título vigente no es un título anterior.
            if nuevo and nuevo != obra.titulo:
                obra.titulos_anteriores.get_or_create(titulo=nuevo)
        return obra


class ObraAdminForm(RegistroVinculoMixin):
    """Mismo autocompletado de Dirección/Producción para el panel /admin.

    Muestra todos los campos de la obra menos los internos del vínculo con el
    registro. Sobre el formulario del titular (ObraForm) agrega a propósito
    `owner` (la titularidad se traspasa), `verificado` (control de la
    Secretaría) y `postulaciones`. Los títulos anteriores se editan con el
    inline, no con los campos sueltos de ObraForm.
    """
    class Meta:
        model = Obra
        exclude = (
            "direccion_content_type", "direccion_object_id",
            "produccion_content_type", "produccion_object_id",
        )


class HitoForm(forms.ModelForm):
    class Meta:
        model = Hito
        fields = [
            "tipo", "nombre", "anio", "fecha", "entidad", "edicion",
            "estado", "resultado", "pais", "lugar", "monto", "moneda",
            "hito_origen", "descripcion", "link", "adjunto",
        ]
        widgets = {
            "tipo":        forms.Select(attrs=_SEL),
            "estado":      forms.Select(attrs=_SEL),
            "nombre":      forms.TextInput(attrs=_TXT),
            "anio":        forms.NumberInput(attrs=_TXT),
            "fecha":       forms.DateInput(attrs={**_TXT, "type": "date"}, format="%Y-%m-%d"),
            "entidad":     forms.TextInput(attrs=_TXT),
            "edicion":     forms.TextInput(attrs=_TXT),
            "resultado":   forms.TextInput(attrs=_TXT),
            "pais":        forms.TextInput(attrs=_TXT),
            "lugar":       forms.TextInput(attrs=_TXT),
            "monto":       forms.NumberInput(attrs=_TXT),
            "moneda":      forms.Select(attrs=_SEL),
            "hito_origen": forms.Select(attrs=_SEL),
            "descripcion": forms.Textarea(attrs={**_TXT, "rows": 3}),
            "link":        forms.URLInput(attrs=_TXT),
            "adjunto":     forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, obra=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].input_formats = ["%Y-%m-%d"]
        # "Surge del hito" solo puede referenciar otros hitos de la misma obra.
        qs = Hito.objects.none()
        if obra is not None:
            qs = Hito.objects.filter(obra=obra)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
        self.fields["hito_origen"].queryset = qs
        self.fields["hito_origen"].required = False
        self.fields["hito_origen"].empty_label = "— (ninguno) —"
        # Campos opcionales en el front (aunque el modelo los permita vacíos).
        for f in ("fecha", "entidad", "edicion", "estado", "resultado", "pais",
                  "lugar", "monto", "moneda", "descripcion", "link", "adjunto"):
            self.fields[f].required = False


class FichaTecnicaForm(forms.ModelForm):
    class Meta:
        model = FichaTecnica
        exclude = ("obra", "fecha_creacion", "fecha_actualizacion")
        widgets = {
            "elenco":                  forms.Textarea(attrs={**_TXT, "rows": 2}),
            "pais":                    forms.TextInput(attrs=_TXT),
            "locaciones_rodaje":       forms.Textarea(attrs={**_TXT, "rows": 2}),
            "idioma":                  forms.TextInput(attrs=_TXT),
            "detalle_financiamiento":  forms.Textarea(attrs={**_TXT, "rows": 2}),
            "resolucion":              forms.Select(attrs=_SEL),
            "relacion_aspecto":        forms.Select(attrs=_SEL),
            "codec_especificaciones":  forms.Textarea(attrs={**_TXT, "rows": 2}),
            "caracteristicas_color":   forms.TextInput(attrs=_TXT),
            "caracteristicas_sonido":  forms.TextInput(attrs=_TXT),
            "medio_entrega":           forms.Select(attrs=_SEL),
            "copyright":               forms.Textarea(attrs={**_TXT, "rows": 2}),
            "notas":                   forms.Textarea(attrs={**_TXT, "rows": 2}),
            "usa_material_archivo":    forms.NullBooleanSelect(attrs=_SEL),
            "origen_archivo":          forms.Textarea(attrs={**_TXT, "rows": 2}),
            "gestion_archivo":         forms.Textarea(attrs={**_TXT, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Toda la ficha es opcional: se completa a medida que hay datos.
        for field in self.fields.values():
            field.required = False


class CreditoForm(RegistroVinculoMixin):
    """Una persona de los créditos: cargo + nombre con vínculo al registro."""

    CONCEPTOS = [
        ("nombre", "nombre_content_type", "nombre_object_id", "nombre_ref"),
    ]

    class Meta:
        model = CreditoFichaTecnica
        fields = ["cargo", "detalle", "nombre"]
        widgets = {
            "cargo":   forms.Select(attrs=_SEL),
            "detalle": forms.TextInput(attrs={**_TXT, "placeholder": "Rol (solo para 'Otro crédito')"}),
            "nombre":  forms.TextInput(attrs={**_TXT, "placeholder": "Nombre y apellido / razón social"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("cargo") == "otro" and not (cleaned.get("detalle") or "").strip():
            self.add_error("detalle", "Especificá el rol para 'Otro crédito'.")
        return cleaned


CreditoFormSet = forms.inlineformset_factory(
    FichaTecnica,
    CreditoFichaTecnica,
    form=CreditoForm,
    extra=1,
    can_delete=True,
)
