from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings


from .validators import validar_pdf, validar_tamano_archivo

from registro_audiovisual.models import PersonaHumana, PersonaJuridica


# ==========================================
# LÍNEAS DE CONVOCATORIA
# ==========================================
LINEAS = [
    ("fomento", "Fomento"),
    ("beneficio", "Beneficio"),
    ("formacion", "Formación"),
    ("incentivo", "Incentivo"),
    ("libre", "Libre"),
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
        # slug único automático si se crea desde cero
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
# POSTULACIÓN (para líneas tipo proyecto)
# ==========================================
class Postulacion(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)

    # ✅ opcional para “línea libre”
    nombre_proyecto = models.CharField(max_length=255, blank=True, null=True)

    TIPO_PROYECTO = [
        ("", "- Seleccionar -"),
        ("", "- Cine -"),
        ("cine_corto", "Cortometraje"),
        ("cine_largo", "Largometraje"),
        ("", "- Serie -"),
        ("serie", "Serie"),
        ("serie_web", "Serie Web"),
        ("", "- Animacion -"),
        ("corto_animacion", "Cortometraje animación"),
        ("largo_animacion", "Largoometraje animación"),
        ("serie_animacion", "Serie animación"),
        ("serieweb_animacion", "Serie web animación"),
        ("videoclip_animacion", "Videoclip animación"),
        ("", "- Otros -"),
        ("tv", "TV"),
        ("publicidad", "Publicidad"),
        ("videoclip", "Videoclip"),
        ("videojuego", "Videojuego"),
        ("transmedia", "Transmedia"),
        ("otro", "Otro"),
    ]
    tipo_proyecto = models.CharField(max_length=50, choices=TIPO_PROYECTO, blank=True)

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
    genero = models.CharField(max_length=50, choices=GENERO, blank=True)

    declaracion_jurada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # NUEVO

    # ✅ ESTA es la fecha real de “clic final”
    fecha_envio = models.DateTimeField(blank=True, null=True)  # CAMBIAR (antes auto_now_add)

    ESTADOS = [
        ("borrador", "Borrador"),
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
        default="borrador" 
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Postulación"
        verbose_name_plural = "Postulaciones"

    def clean(self):
        """
        Regla clave:
        - Si la convocatoria NO es línea libre → exigir datos de proyecto
        - Si es línea libre → permitir vacío
        """
        super().clean()

        if self.convocatoria and self.convocatoria.linea != "libre":
            if not self.nombre_proyecto:
                raise ValidationError({"nombre_proyecto": "Campo obligatorio para esta convocatoria."})
            if not self.tipo_proyecto:
                raise ValidationError({"tipo_proyecto": "Campo obligatorio para esta convocatoria."})
            if not self.genero:
                raise ValidationError({"genero": "Campo obligatorio para esta convocatoria."})

    def __str__(self):
        nombre = self.nombre_proyecto or "(Sin título)"
        return f"{nombre} – {self.user.username}"


# ==========================================
# DOCUMENTOS DE POSTULACIÓN
# ==========================================
class DocumentoPostulacion(models.Model):

    TIPOS = [
        ("PERSONAL", "Documentación personal"),
        ("PROYECTO", "Documentación del proyecto"),
        ("SUBSANADO", "Documentación subsanada"),
    ]

    SUBTIPOS_SUBSANADO = [
    ("PROYECTO", "Subsanación de proyecto"),
    ("ADMIN", "Subsanación administrativa"),
    ]

    ESTADOS = [
        ("PENDIENTE", "Pendiente de envío"),
        ("ENVIADO", "Enviado"),
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

    subtipo_subsanado = models.CharField(
        max_length=20,
        choices=SUBTIPOS_SUBSANADO,
        blank=True,
        null=True,
        db_index=True,
        help_text="Solo se usa cuando el tipo es SUBSANADO",
    )


    # ✅ NUEVO
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="PENDIENTE",
        db_index=True,
    )

    archivo = models.FileField(
        upload_to="postulaciones/documentos/",
        validators=[validar_pdf, validar_tamano_archivo],
    )

    fecha_subida = models.DateTimeField(auto_now_add=True)

    # (opcional, pero útil) fecha de confirmación real
    fecha_envio = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.postulacion_id} · {self.get_tipo_display()} · {self.get_estado_display()}"



# ==========================================
# FORMACIÓN — INSCRIPCIÓN (sin obligar Registro Audiovisual)
# ==========================================
class InscripcionFormacion(models.Model):
    """
    Si el usuario YA está en Registro Audiovisual:
      - vincula persona_humana o persona_juridica y no repite datos.

    Si NO está:
      - guarda datos mínimos de contacto y perfil.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)

    persona_humana = models.ForeignKey(PersonaHumana, on_delete=models.SET_NULL, null=True, blank=True)
    persona_juridica = models.ForeignKey(PersonaJuridica, on_delete=models.SET_NULL, null=True, blank=True)

    nombre = models.CharField(max_length=120, blank=True)
    apellido = models.CharField(max_length=120, blank=True)
    dni = models.CharField(max_length=30, blank=True)

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=60, blank=True)

    # ✅ Localidad con lista de municipios (mismos códigos que venís usando)
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

    localidad = models.CharField(max_length=20, choices=LOCALIDADES, blank=True)
    otra_localidad = models.CharField(max_length=120, blank=True)

    VINCULO_SECTOR = [
        ("sector", "Trabajo actualmente en el sector audiovisual"),
        ("empezando", "Estoy empezando / quiero insertarme"),
        ("no_sector", "No, pero quiero capacitarme"),
    ]
    vinculo_sector = models.CharField(max_length=20, choices=VINCULO_SECTOR, blank=True)

    declaracion_jurada = models.BooleanField(default=False)

    ESTADOS = [
        ("inscripto", "Inscripto"),
        ("admitido", "Admitido"),
        ("no_admitido", "No admitido"),
        ("lista_espera", "Lista de espera"),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default="inscripto")

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "convocatoria")
        ordering = ["-fecha"]
        verbose_name = "Inscripción a formación"
        verbose_name_plural = "Inscripciones a formación"

    def clean(self):
        super().clean()

        # durante form.is_valid() puede no estar seteada convocatoria todavía
        if not self.convocatoria_id:
            return

        if self.convocatoria.linea != "formacion":
            raise ValidationError("Esta inscripción solo corresponde a convocatorias de línea Formación.")

        if self.persona_humana_id and self.persona_juridica_id:
            raise ValidationError("La inscripción no puede vincular Persona Humana y Persona Jurídica al mismo tiempo.")

        tiene_registro = bool(self.persona_humana_id or self.persona_juridica_id)
        if not tiene_registro:
            if not self.email:
                raise ValidationError({"email": "Ingresá un email de contacto."})
            if not self.telefono:
                raise ValidationError({"telefono": "Ingresá un teléfono de contacto."})

        # si elige "Otro", exigir texto
        if self.localidad == "otro" and not self.otra_localidad.strip():
            raise ValidationError({"otra_localidad": "Indicá tu localidad."})

    def __str__(self):
        titulo = self.convocatoria.titulo if self.convocatoria_id else "(sin convocatoria)"
        return f"{self.user.username} → {titulo} ({self.estado})"



# ==========================================
# INSCRIPCIÓN A CURSOS (existente)
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


# ==========================================
# OBSERVACIONES ADMINISTRATIVAS
# ==========================================
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

    def __str__(self):
        return f"{self.postulacion_id} · {self.get_tipo_documento_display()} · {'OK' if self.subsanada else 'Pendiente'}"


# ==========================================
# ASIGNACIÓN JURADO ⇄ CONVOCATORIA
# ==========================================
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


# ==========================================
# ARCHIVO POSTULACIÓN (sin relación; lo dejo)
# ==========================================
class ArchivoPostulacion(models.Model):

    archivo = models.FileField(
        upload_to="convocatorias/archivos/",
        validators=[validar_pdf, validar_tamano_archivo],
        verbose_name="Archivo del proyecto (PDF)"
    )

    def __str__(self):
        return self.archivo.name or "ArchivoPostulacion"


# ==========================================
# RENDICION
# ==========================================

try:
    from django.db.models import JSONField  # Django < 4.1 (si aplica)
except Exception:
    JSONField = None


class Rendicion(models.Model):

    ESTADOS = (
        ("BORRADOR", "Borrador"),
        ("ENVIADO", "Enviado"),
        ("OBSERVADO", "Observado"),
        ("SUBSANADO", "Subsanado"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
    )

    FISICO_ESTADOS = (
        ("PENDIENTE", "Pendiente"),
        ("RECIBIDO", "Recibido"),
        ("OBSERVADO", "Observado"),
        ("APROBADO", "Aprobado"),
    )

    postulacion = models.OneToOneField(
        "convocatorias.Postulacion",
        on_delete=models.CASCADE,
        related_name="rendicion",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Digital
    link_documentacion = models.URLField(blank=True)
    observaciones_usuario = models.TextField(blank=True)
    observaciones_admin = models.TextField(blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="BORRADOR")

    # Físico (paralelo)
    fisico_estado = models.CharField(max_length=20, choices=FISICO_ESTADOS, default="PENDIENTE")
    fisico_fecha_recepcion = models.DateField(null=True, blank=True)
    fisico_observaciones = models.TextField(blank=True)

    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_ultima_revision = models.DateTimeField(null=True, blank=True)

    # Bitácora liviana
    historial = models.JSONField(default=list, blank=True)

    def add_event(self, actor, action, detail=""):
        """
        actor: 'usuario' / 'admin' / 'sistema'
        action: texto corto (ENVIADO, OBSERVADO, LINK_ACTUALIZADO, etc.)
        detail: texto libre
        """
        self.historial.append({
            "ts": timezone.now().isoformat(),
            "actor": actor,
            "action": action,
            "detail": detail,
        })

    def __str__(self):
        return f"Rendición - Postulación {self.postulacion_id} ({self.estado})"