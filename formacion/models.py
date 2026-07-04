from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from .validators import validar_documento_admitido, validar_tamano_archivo


# ==========================================
# CHOICES
# ==========================================

TIPO_FORMACION = [
    ("ASINCRONICA",          "Asincrónica (link público al curso)"),
    ("INSCRIPCION_LIBRE",    "Inscripción sin registro audiovisual"),
    ("INSCRIPCION_REGISTRO", "Inscripción con registro audiovisual"),
]

BLOQUE_PERSONAS_TITULO = [
    ("FORMADORES", "Formadores/as"),
    ("TUTORES",    "Tutores/as"),
    ("NINGUNO",    "Sin título"),
]

LOCALIDADES = [
    ("", "- Seleccionar -"),
    ("SC", "Salta Capital"),
    ("otro", "Otro"),
    ("Ag", "Aguaray"),
    ("AB", "Aguas Blancas"),
    ("An", "Angastaco"),
    ("Ai", "Animaná"),
    ("AS", "Apolinario Saravia"),
    ("Ca", "Cachi"),
    ("Cf", "Cafayate"),
    ("CQ", "Campo Quijano"),
    ("CS", "Campo Santo"),
    ("Ce", "Cerrillos"),
    ("Ch", "Chicoana"),
    ("CSR", "Colonia Santa Rosa"),
    ("CM", "Coronel Moldes"),
    ("EB", "El Bordo"),
    ("EC", "El Carril"),
    ("EG", "El Galpón"),
    ("EJ", "El Jardín"),
    ("EM", "El Molinar"),
    ("ET", "El Tala"),
    ("Gi", "General Güemes"),
    ("GM", "General Mosconi"),
    ("Ga", "Gaona"),
    ("Gp", "Guachipas"),
    ("Hi", "Hipólito Yrigoyen"),
    ("I", "Iruya"),
    ("JV", "Joaquín V. González"),
    ("LL", "La Caldera"),
    ("LC", "La Candelaria"),
    ("LV", "La Viña"),
    ("LM", "Las Lajitas"),
    ("LS", "Los Toldos"),
    ("LR", "Rosario de Lerma"),
    ("LP", "La Poma"),
    ("LQ", "La Quesera"),
    ("MA", "Metán"),
    ("Mi", "Molinos"),
    ("NP", "Nazareno"),
    ("OC", "Orán"),
    ("Pa", "Payogasta"),
    ("Pi", "Pichanal"),
    ("Po", "Posadas"),
    ("Ri", "Rivadavia"),
    ("RN", "Rosario de la Frontera"),
    ("RS", "Rosario de Santa Fe"),
    ("SA", "San Antonio de los Cobres"),
    ("SL", "San Carlos"),
    ("SO", "San Lorenzo"),
    ("SP", "San Ramón de la Nueva Orán"),
    ("ST", "Santa Victoria Este"),
    ("Se", "Seclantás"),
    ("Ta", "Tartagal"),
    ("To", "Tolombón"),
    ("Ur", "Urundel"),
    ("Va", "Vaqueros"),
]

VINCULO_SECTOR = [
    ("sector",    "Trabajo actualmente en el sector audiovisual"),
    ("empezando", "Estoy empezando / quiero insertarme"),
    ("no_sector", "No, pero quiero capacitarme"),
]

GENERO = [
    ("",                  "- Seleccionar -"),
    ("masculino",         "Masculino"),
    ("femenino",          "Femenino"),
    ("no_binario",        "No binario"),
    ("otro",              "Otro"),
    ("prefiero_no_decir", "Prefiero no decirlo"),
]

ESTADOS = [
    ("inscripto",    "Inscripto"),
    ("observado",    "Observado"),
    ("admitido",     "Admitido"),
    ("no_admitido",  "No admitido"),
    ("lista_espera", "Lista de espera"),
]


# ==========================================
# CONVOCATORIA DE FORMACIÓN
# ==========================================

class ConvocatoriaFormacion(models.Model):
    titulo            = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, blank=True)
    tipo_formacion    = models.CharField(max_length=25, choices=TIPO_FORMACION, default="INSCRIPCION_LIBRE")
    descripcion_corta = models.TextField(blank=True)
    descripcion_larga = models.TextField(blank=True)
    tematica_genero   = models.CharField(max_length=200, blank=True)
    requisitos        = models.TextField(blank=True)
    beneficios        = models.TextField(blank=True)
    bases_pdf         = models.FileField(
        upload_to="formacion/bases/", blank=True, null=True,
        validators=[validar_documento_admitido, validar_tamano_archivo],
        verbose_name="Bases (PDF / Excel / Planilla)",
    )
    imagen     = models.ImageField(upload_to="formacion/img/", blank=True, null=True)
    url_curso  = models.URLField("URL del curso asincrónico", blank=True, null=True)
    url_destino = models.CharField(max_length=300, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    bloque_personas = models.CharField(
        max_length=20, choices=BLOQUE_PERSONAS_TITULO, default="FORMADORES"
    )
    cupo_maximo = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Cupo máximo",
        help_text="Dejá en blanco para inscripciones ilimitadas.",
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "-fecha_inicio"]
        verbose_name = "Convocatoria de formación"
        verbose_name_plural = "Convocatorias de formación"

    @property
    def vigente(self):
        hoy = timezone.localdate()
        return self.fecha_inicio <= hoy <= self.fecha_fin

    def save(self, *args, **kwargs):
        if self._state.adding and self.titulo:
            base_slug = slugify(self.titulo)
            slug = base_slug
            counter = 1
            while ConvocatoriaFormacion.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


# ==========================================
# MIEMBROS (formadores / tutores)
# ==========================================

class MiembroFormador(models.Model):
    convocatoria = models.ForeignKey(
        ConvocatoriaFormacion,
        on_delete=models.CASCADE,
        related_name="miembros",
    )
    nombre = models.CharField(max_length=200)
    bio    = models.TextField(blank=True)
    foto   = models.ImageField(upload_to="formacion/formadores/", blank=True, null=True)
    orden  = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Formador/a"
        verbose_name_plural = "Formadores/as"

    def __str__(self):
        return self.nombre


# ==========================================
# CONFIGURACIÓN DE INSCRIPCIÓN
# ==========================================

class ConfiguracionInscripcionFormacion(models.Model):
    convocatoria = models.OneToOneField(
        ConvocatoriaFormacion,
        on_delete=models.CASCADE,
        related_name="config_inscripcion",
    )
    mostrar_nombre_apellido = models.BooleanField(default=True,  verbose_name="Nombre y apellido")
    mostrar_dni             = models.BooleanField(default=True,  verbose_name="DNI")
    mostrar_genero          = models.BooleanField(default=False, verbose_name="Género")
    mostrar_edad            = models.BooleanField(default=False, verbose_name="Edad")
    mostrar_telefono        = models.BooleanField(default=True,  verbose_name="Teléfono")
    mostrar_email           = models.BooleanField(default=True,  verbose_name="Correo electrónico")
    mostrar_documentacion   = models.BooleanField(default=False, verbose_name="Subir documentación")

    class Meta:
        verbose_name = "Configuración de inscripción (formación)"
        verbose_name_plural = "Configuraciones de inscripción (formación)"

    def __str__(self):
        return f"Config inscripción → {self.convocatoria.titulo}"


# ==========================================
# INSCRIPCIÓN
# ==========================================

class InscripcionFormacion(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(ConvocatoriaFormacion, on_delete=models.CASCADE)

    persona_humana   = models.ForeignKey(PersonaHumana,   on_delete=models.SET_NULL, null=True, blank=True)
    persona_juridica = models.ForeignKey(PersonaJuridica, on_delete=models.SET_NULL, null=True, blank=True)

    nombre         = models.CharField(max_length=120, blank=True)
    apellido       = models.CharField(max_length=120, blank=True)
    dni            = models.CharField(max_length=30, blank=True)
    email          = models.EmailField(blank=True)
    telefono       = models.CharField(max_length=60, blank=True)
    localidad      = models.CharField(max_length=20, choices=LOCALIDADES, blank=True)
    otra_localidad = models.CharField(max_length=120, blank=True)
    vinculo_sector = models.CharField(max_length=20, choices=VINCULO_SECTOR, blank=True)
    genero         = models.CharField(max_length=20, choices=GENERO, blank=True)
    edad           = models.PositiveSmallIntegerField(null=True, blank=True)

    documentacion = models.FileField(
        upload_to="formacion/documentacion/",
        blank=True, null=True,
        validators=[validar_documento_admitido, validar_tamano_archivo],
        verbose_name="Documentación",
    )

    declaracion_jurada = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="inscripto")
    fecha  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "convocatoria")
        ordering = ["-fecha"]
        verbose_name = "Inscripción a formación"
        verbose_name_plural = "Inscripciones a formación"

    def clean(self):
        super().clean()

        if self.persona_humana_id and self.persona_juridica_id:
            raise ValidationError(
                "La inscripción no puede vincular Persona Humana y Persona Jurídica al mismo tiempo."
            )

        if self.localidad == "otro" and not (self.otra_localidad or "").strip():
            raise ValidationError({"otra_localidad": "Indicá tu localidad."})

    def __str__(self):
        titulo = self.convocatoria.titulo if self.convocatoria_id else "(sin convocatoria)"
        return f"{self.user.username} → {titulo} ({self.estado})"


# ==========================================
# OBSERVACIÓN ADMINISTRATIVA (FORMACIÓN)
# ==========================================

class ObservacionFormacion(models.Model):
    inscripcion = models.ForeignKey(
        InscripcionFormacion,
        on_delete=models.CASCADE,
        related_name="observaciones",
    )
    descripcion = models.CharField(
        max_length=255,
        help_text="Ej: Falta DNI, Falta comprobante de pago",
    )
    creada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    subsanada      = models.BooleanField(default=False)

    class Meta:
        ordering = ["fecha_creacion"]
        verbose_name = "Observación administrativa (formación)"
        verbose_name_plural = "Observaciones administrativas (formación)"

    def __str__(self):
        return f"Inscripción {self.inscripcion_id} · {'OK' if self.subsanada else 'Pendiente'}"
