from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


# ==============================
# MODELOS EXISTENTES (igual)
# ==============================

class PostulacionIDEA(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    linea_fomento = models.CharField(max_length=50)
    nombre_proyecto = models.CharField(max_length=255)
    tipo_proyecto = models.CharField(max_length=50)
    genero = models.CharField(max_length=50)
    duracion_minutos = models.PositiveIntegerField()

    declaracion_jurada = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    ESTADOS = [
        ('ENVIADA', 'Enviada'),
        ('REVISION', 'En revisión'),
        ('SUBSANAR', 'Subsanar'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ENVIADA')

    def __str__(self):
        return f"{self.nombre_proyecto} - {self.user.username}"


class DocumentoPersonal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="documentacion/personal/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doc personal de {self.user.username}"


class DocumentoProyecto(models.Model):
    postulacion = models.ForeignKey(
        PostulacionIDEA,
        on_delete=models.CASCADE,
        related_name="documentos_proyecto"
    )
    archivo = models.FileField(upload_to="documentacion/proyecto/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doc proyecto #{self.postulacion.id}"


# ==============================
# CONVOCATORIAS
# ==============================

CATEGORIAS = [
    ("CONCURSO", "Concurso"),
    ("PROGRAMA", "Programa"),
    ("SUBSIDIO", "Subsidio"),
    ("CURSO", "Curso / Capacitación"),
    ("INCENTIVO", "Incentivo"),
    ("BENEFICIO", "Beneficio"),
]

BLOQUE_PERSONAS_TITULO = [
    ("JURADO", "Jurado"),
    ("FORMADORES", "Formadores"),
    ("TUTORES", "Tutores"),
    ("NINGUNO", "Sin título"),
]

class Jurado(models.Model):
    nombre = models.CharField(max_length=200)
    foto = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)

    def __str__(self):
        return self.nombre


class Convocatoria(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    descripcion_corta = models.TextField(blank=True)
    descripcion_larga = models.TextField(blank=True)  # ← NUEVO

    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    tematica_genero = models.CharField(max_length=200, blank=True)

    requisitos = models.TextField(blank=True)
    beneficios = models.TextField(blank=True)
    bases_pdf = models.FileField(upload_to="convocatorias/bases/", blank=True, null=True)

    imagen = models.ImageField(upload_to="convocatorias/img/", blank=True, null=True)

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


    orden = models.PositiveIntegerField(default=0)  # ← NUEVO (para ordenar carrusel)

    url_destino = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["orden", "-fecha_inicio"]

    @property
    def vigente(self):
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin

    def save(self, *args, **kwargs):
        if not self.slug and self.titulo:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo