from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from .validators import validar_pdf, validar_tamano_archivo


# ==========================================
# LÍNEAS DE CONVOCATORIA
# ==========================================
LINEAS = [
    ("fomento", "Fomento"),
    ("beneficio", "Beneficio"),
    ("formacion", "Formación"),
    ("incentivo", "Incentivo"),
]


# ==========================================
# CATEGORÍAS
# ==========================================
CATEGORIAS = [
    ("CONCURSO", "Concurso"),
    ("PROGRAMA", "Programa"),
    ("SUBSIDIO", "Subsidio"),
    ("CURSO", "Curso / Capacitación"),
    ("INCENTIVO", "Incentivo"),
    ("BENEFICIO", "Beneficio"),
]


# ==========================================
# BLOQUE PERSONAS (jurado / formadores)
# ==========================================
BLOQUE_PERSONAS_TITULO = [
    ("JURADO", "Jurado"),
    ("FORMADORES", "Formadores"),
    ("TUTORES", "Tutores"),
    ("NINGUNO", "Sin título"),
]


# ==========================================
# JURADOS (opcional)
# ==========================================
class Jurado(models.Model):
    nombre = models.CharField(max_length=200)
    foto = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)

    def __str__(self):
        return self.nombre


# ==========================================
# CONVOCATORIA
# ==========================================
class Convocatoria(models.Model):

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    descripcion_corta = models.TextField(blank=True)
    descripcion_larga = models.TextField(blank=True)

    url_curso = models.URLField(
        "URL del curso asincrónico",
        blank=True,
        null=True,
        help_text="Solo completar si el curso es asincrónico."
    )

    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    tematica_genero = models.CharField(max_length=200, blank=True)

    linea = models.CharField(max_length=20, choices=LINEAS)

    requisitos = models.TextField(blank=True)
    beneficios = models.TextField(blank=True)

    bases_pdf = models.FileField(
        upload_to="convocatorias/bases/",
        blank=True,
        null=True
    )

    imagen = models.ImageField(
        upload_to="convocatorias/img/",
        blank=True,
        null=True
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    bloque_personas = models.CharField(
        max_length=20,
        choices=BLOQUE_PERSONAS_TITULO,
        default="JURADO"
    )

    jurado1_nombre = models.CharField(max_length=200, blank=True)
    jurado1_foto = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)
    jurado1_bio = models.TextField(blank=True)

    jurado2_nombre = models.CharField(max_length=200, blank=True)
    jurado2_foto = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)
    jurado2_bio = models.TextField(blank=True)

    jurado3_nombre = models.CharField(max_length=200, blank=True)
    jurado3_foto = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)
    jurado3_bio = models.TextField(blank=True)

    orden = models.PositiveIntegerField(default=0)
    url_destino = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["orden", "-fecha_inicio"]

    @property
    def vigente(self):
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin

    def save(self, *args, **kwargs):
        if self._state.adding and self.titulo:
            base_slug = slugify(self.titulo)
            slug = base_slug
            counter = 1

            while Convocatoria.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"

            self.slug = slug

        super().save(*args, **kwargs)



    def __str__(self):
        return self.titulo


# ==========================================
# POSTULACIÓN
# ==========================================
class Postulacion(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)

    nombre_proyecto = models.CharField(max_length=255)

    TIPO_PROYECTO = [
        ('', '- Seleccionar -'),
        ('', '- Cine -'),
        ("cine_corto", "Cortometraje"),
        ("cine_largo", "Largometraje"),
        ('', '- Serie -'),
        ("serie", "Serie"),
        ("serie_web", "Serie Web"),
        ('', '- Animacion -'),
        ("corto_animacion", "Cortometraje animación"),
        ("largo_animacion", "Largoometraje animación"),
        ("serie_animacion", "Serie animación"),
        ("serieweb_animacion", "Serie web animación"),
        ("videoclip_animacion", "Videoclip animación"),
        ('', '- Otros -'),
        ("tv", "TV"),
        ("publicidad", "Publicidad"),
        ("videoclip", "Videoclip"),
        ("videojuego", "Videojuego"),
        ("transmedia", "Transmedia"),
        ("otro", "Otro"),
    ]
    tipo_proyecto = models.CharField(max_length=50, choices=TIPO_PROYECTO)

    GENERO = [
        ("ficcion", "Ficción"),
        ("documental", "Documental"),
        ("noficcion", "No ficción"),
        ("educativo", "Educativo"),
        ("deportivo", "Deportivo"),
        ("simulacion", "Simulacion"),
        ("ludico", "Lúdico"),
        ("otro", "Otro"),
    ]
    genero = models.CharField(max_length=50, choices=GENERO)

    declaracion_jurada = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    ESTADOS = [
        ("enviado", "Enviado"),
        ("revision_admin", "En revisión administrativa"),
        ("observado", "Observado (requiere subsanación)"),
        ("admitido", "Admitido"),
        ("evaluacion_jurado", "En evaluación por jurado"),
        ("seleccionado", "Seleccionado"),
        ("no_seleccionado", "No seleccionado"),
        ("finalizado", "Finalizado"),
    ]

    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default="enviado"
    )

    class Meta:
        ordering = ["-fecha_envio"]
        verbose_name = "Postulación"
        verbose_name_plural = "Postulaciones"

    def __str__(self):
        return f"{self.nombre_proyecto} – {self.user.username}"


# ==========================================
# DOCUMENTOS DE POSTULACIÓN (ÚNICO MODELO)
# ==========================================
class DocumentoPostulacion(models.Model):

    TIPOS = [
        ("PERSONAL", "Documentación personal"),
        ("PROYECTO", "Documentación del proyecto"),
        ("SUBSANADO", "Documentación subsanada"),
    ]

    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="documentos"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    archivo = models.FileField(
    upload_to="postulaciones/documentos/",
    validators=[validar_pdf, validar_tamano_archivo],
)
    fecha_subida = models.DateTimeField(auto_now_add=True)


# ==========================================
# INSCRIPCIÓN A CURSOS
# ==========================================
class InscripcionCurso(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "convocatoria")
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.user.username} → {self.convocatoria.titulo}"



class ObservacionAdministrativa(models.Model):

    TIPOS_DOCUMENTO = [
        ("PERSONAL", "Documentación personal"),
        ("PROYECTO", "Documentación del proyecto"),
    ]

    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="observaciones"
    )

    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPOS_DOCUMENTO,
        help_text="Tipo de documentación a subsanar"
    )

    descripcion = models.CharField(
        max_length=255,
        help_text="Ej: Falta DNI, Falta CBU, Presupuesto sin firma"
    )

    creada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    subsanada = models.BooleanField(default=False)


# convocatorias/models.py



class AsignacionJuradoConvocatoria(models.Model):
    jurado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"groups__name": "jurado"},
        verbose_name="Jurado"
    )

    convocatoria = models.ForeignKey(
        Convocatoria,
        on_delete=models.CASCADE,
        verbose_name="Convocatoria asignada"
    )

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("jurado", "convocatoria")
        verbose_name = "Asignación de jurado a convocatoria"
        verbose_name_plural = "Asignaciones de jurados a convocatorias"

    def __str__(self):
        return f"{self.jurado.username} → {self.convocatoria.titulo}"





class ArchivoPostulacion(models.Model):

    archivo = models.FileField(
        upload_to="convocatorias/archivos/",
        validators=[validar_pdf, validar_tamano_archivo],
        verbose_name="Archivo del proyecto (PDF)"
    )