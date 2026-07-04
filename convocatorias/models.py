from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .validators import validar_documento_admitido, validar_tamano_archivo

cbu_validator = RegexValidator(
    regex=r'^\d{22}$',
    message='El CBU debe tener exactamente 22 dígitos numéricos.',
)

from registro_audiovisual.models import PersonaHumana, PersonaJuridica


# ==========================================
# LÍNEAS DE CONVOCATORIA
# ==========================================
LINEAS = [
    ("fomento",    "Fomento"),
    ("cash_rebate","Cash Rebate"),
    ("exencion",   "Exención impositiva"),  # gestionado por la app exencion
]


# ==========================================
# CATEGORÍAS
# ==========================================
CATEGORIAS = [
    ("CONCURSO", "Concurso"),
    ("PROGRAMA", "Programa"),
    ("SUBSIDIO", "Subsidio"),
    ("CURSO",    "Curso / Capacitación"),
    ("BENEFICIO","Beneficio"),
]


# ==========================================
# BLOQUE PERSONAS (jurado / formadores)
# ==========================================
BLOQUE_PERSONAS_TITULO = [
    ("JURADO",      "Jurado"),
    ("FORMADORES",  "Formadores/as"),
    ("TUTORES",     "Tutores/as"),
    ("NINGUNO",     "Sin título"),
]


# ==========================================
# CONVOCATORIA
# ==========================================
class Convocatoria(models.Model):

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    descripcion_corta = models.TextField(blank=True)
    descripcion_larga = models.TextField(blank=True)

    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    tematica_genero = models.CharField(max_length=200, blank=True)

    linea = models.CharField(max_length=20, choices=LINEAS)

    requisitos = models.TextField(blank=True)
    beneficios = models.TextField(blank=True)

    bases_pdf = models.FileField(
        upload_to="convocatorias/bases/",
        blank=True,
        null=True,
        validators=[validar_documento_admitido, validar_tamano_archivo],
        verbose_name="Bases (PDF / Excel / Planilla)"
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

    orden = models.PositiveIntegerField(default=0)
    url_destino = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["orden", "-fecha_inicio"]

    @property
    def vigente(self):
        hoy = timezone.localdate()
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
# MIEMBROS DEL JURADO (bloque público de la convocatoria)
# ==========================================
class MiembroJurado(models.Model):
    convocatoria = models.ForeignKey(
        Convocatoria,
        on_delete=models.CASCADE,
        related_name="miembros_jurado",
    )
    nombre = models.CharField(max_length=200)
    foto   = models.ImageField(upload_to="convocatorias/jurados/", blank=True, null=True)
    bio    = models.TextField(blank=True)
    orden  = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "Miembro del jurado"
        verbose_name_plural = "Miembros del jurado"

    def __str__(self):
        return f"{self.nombre} — {self.convocatoria}"


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
        ("largo_animacion", "Largometraje animación"),
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

    # ── Datos del equipo ────────────────────────────────────
    cbu = models.CharField(
        "CBU",
        max_length=22,
        blank=True,
        validators=[cbu_validator],
        help_text="CBU del productor/presentante (22 dígitos). Solo requerido si la convocatoria lo exige.",
    )

    # ── Datos del proyecto ───────────────────────────────────
    sinopsis_corta = models.TextField(
        "Logline / Sinopsis corta",
        blank=True,
        max_length=3000,
        help_text="Máximo 3000 caracteres.",
    )

    link_pitch = models.URLField(
        "Link al pitch",
        blank=True,
        help_text="URL del pitch del proyecto (YouTube, Vimeo, Drive, etc.)",
    )

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
        ("no_admitido", "No admitido"),
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
        super().clean()
        if self.declaracion_jurada is False and self.estado == "enviado":
            raise ValidationError("No se puede enviar la postulación sin aceptar la declaración jurada.")

    def __str__(self):
        nombre = self.nombre_proyecto or "(Sin título)"
        return f"{nombre} – {self.user.username}"


# ==========================================
# DOCUMENTOS DE POSTULACIÓN
# ==========================================
class DocumentoPostulacion(models.Model):

    TIPOS = [
        # ── Existentes ──────────────────────────────────────
        ("PERSONAL", "Documentación personal (genérica)"),
        ("PROYECTO", "Documentación del proyecto (genérica)"),
        ("SUBSANADO", "Documentación subsanada"),
        # ── Productor ───────────────────────────────────────
        ("COMPROBANTE_CBU", "Comprobante de CBU"),
        # ── Proyecto ────────────────────────────────────────
        ("GUION",                 "Guion"),
        ("DOSSIER",               "Dossier del proyecto"),
        ("MATERIAL_ADICIONAL",    "Material adicional"),
        ("PLANILLA_OFICIAL",      "Planilla oficial (presupuesto / plan financiero / equipo / aportes)"),
        ("REGISTRO_DNDA",         "Registro de la obra en DNDA"),
        ("AUTORIZACION_DERECHOS", "Autorización de derechos"),
        ("NOTA_INTENCION",        "Nota de intención / documentación"),
        ("DOCUMENTACION",         "Documentación"),
        # ── Apoyo a participación ────────────────────────────
        ("CARTA_INTENCION",       "Carta de intención"),
        ("CONSTANCIA_INVITACION", "Constancia de invitación/participación"),
        # ── Persona jurídica ─────────────────────────────────
        ("ESTATUTO",              "Estatuto / instrumento constitutivo"),
        ("CONSTANCIA_ARCA_JUR",   "Constancia ARCA persona jurídica"),
        ("DNI_REPRESENTANTE",     "DNI del representante legal"),
        ("DNI_PRODUCTOR_RESP",    "DNI del productor/a responsable"),
        ("ACTA_AUTORIDADES",      "Acta de designación de autoridades"),
        ("CONTRATO_COPRODUCTORA", "Contrato con empresa coproductora"),
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
        max_length=30,
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
        validators=[validar_documento_admitido, validar_tamano_archivo],
    )


    fecha_subida = models.DateTimeField(auto_now_add=True)

    # (opcional, pero útil) fecha de confirmación real
    fecha_envio = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.postulacion_id} · {self.get_tipo_display()} · {self.get_estado_display()}"




# ==========================================
# OBSERVACIONES ADMINISTRATIVAS
# ==========================================
class ObservacionAdministrativa(models.Model):

    TIPOS_DOCUMENTO = [
        ("PERSONAL", "Documentación personal"),
        ("CBU",      "Comprobante de CBU"),
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

    doble_ciego      = models.BooleanField(
        "Doble ciego",
        default=False,
        help_text="Si está activo, el jurado no ve el equipo de la postulación.",
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("jurado", "convocatoria")
        verbose_name = "Asignación de jurado a convocatoria"
        verbose_name_plural = "Asignaciones de jurados a convocatorias"

    def __str__(self):
        return f"{self.jurado.username} → {self.convocatoria.titulo}"



# ==========================================
# CONFIGURACIÓN DE POSTULACIÓN POR CONVOCATORIA
# ==========================================
class ConfiguracionPostulacion(models.Model):
    """
    Define qué secciones y documentos son obligatorios en cada convocatoria.
    Creada automáticamente al guardar una Convocatoria desde el admin.
    """
    convocatoria = models.OneToOneField(
        Convocatoria,
        on_delete=models.CASCADE,
        related_name="configuracion",
    )

    # ── Tipo de postulante ───────────────────────────────────
    TIPO_POSTULANTE = [
        ("HUMANA",   "Solo persona humana"),
        ("JURIDICA", "Solo persona jurídica"),
        ("AMBAS",    "Persona humana o jurídica"),
    ]
    tipo_postulante = models.CharField(
        max_length=10,
        choices=TIPO_POSTULANTE,
        default="HUMANA",
        verbose_name="Tipo de postulante admitido",
    )

    # ── Equipo ───────────────────────────────────────────────
    requiere_productor_responsable = models.BooleanField(default=False, verbose_name="Requiere productor/a responsable (persona jurídica)")
    requiere_director        = models.BooleanField(default=False, verbose_name="Requiere director/a")
    director_puede_coincidir = models.BooleanField(default=False, verbose_name="El/la director/a puede ser la misma persona que el/la productor/a presentante")
    requiere_guionista       = models.BooleanField(default=False, verbose_name="Requiere guionista")
    requiere_realizador      = models.BooleanField(default=False, verbose_name="Requiere realizador/a")
    requiere_cbu             = models.BooleanField(default=True,  verbose_name="Requiere CBU")

    # ── Proyecto — campos de texto ───────────────────────────
    mostrar_titulo          = models.BooleanField(default=True,  verbose_name="Título del proyecto")
    mostrar_formato         = models.BooleanField(default=True,  verbose_name="Formato (tipo de proyecto)")
    mostrar_genero          = models.BooleanField(default=True,  verbose_name="Género")
    requiere_sinopsis       = models.BooleanField(default=False, verbose_name="Logline / Sinopsis corta")
    requiere_link_pitch     = models.BooleanField(default=False, verbose_name="Link al pitch")

    # ── Proyecto — documentos (todos opcionales para el postulante) ──
    mostrar_guion                   = models.BooleanField(default=False, verbose_name="Mostrar sección: Guion")
    mostrar_dossier                 = models.BooleanField(default=False, verbose_name="Mostrar sección: Dossier")
    mostrar_material_adicional      = models.BooleanField(default=False, verbose_name="Mostrar sección: Material adicional")
    mostrar_planilla_oficial        = models.BooleanField(default=False, verbose_name="Mostrar sección: Planilla oficial")
    mostrar_dnda                    = models.BooleanField(default=False, verbose_name="Mostrar sección: Registro DNDA")
    mostrar_autorizacion_derechos   = models.BooleanField(default=False, verbose_name="Mostrar sección: Autorización de derechos")
    mostrar_nota_intencion          = models.BooleanField(default=False, verbose_name="Mostrar sección: Nota de intención")
    mostrar_carta_intencion         = models.BooleanField(default=False, verbose_name="Mostrar sección: Carta de intención")
    mostrar_constancia_invitacion   = models.BooleanField(default=False, verbose_name="Mostrar sección: Constancia de invitación")
    mostrar_documentacion           = models.BooleanField(default=False, verbose_name="Mostrar sección: Documentación (genérica)")

    # ── Planilla oficial ─────────────────────────────────────
    planilla_archivo = models.FileField(
        upload_to="convocatorias/planillas/",
        blank=True,
        null=True,
        verbose_name="Archivo de planilla oficial (.xlsx)",
        help_text="Planilla xlsx que el presentante descarga, completa offline y sube al postularse.",
    )

    class Meta:
        verbose_name = "Configuración de postulación"
        verbose_name_plural = "Configuraciones de postulación"

    def __str__(self):
        return f"Config → {self.convocatoria.titulo}"


# ==========================================
# INTEGRANTES DEL EQUIPO POR POSTULACIÓN
# ==========================================
class IntegrantePostulacion(models.Model):
    """
    Registra cada integrante del equipo declarado en una postulación.
    El productor siempre es el usuario logueado (Opción A).
    Director, guionista y realizador se buscan en PersonaHumana del registro.
    """

    ROLES = [
        ("PRODUCTOR",   "Productor/a"),
        ("DIRECTOR",    "Director/a"),
        ("GUIONISTA",   "Guionista"),
        ("REALIZADOR",  "Realizador/a integral"),
    ]

    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="integrantes",
    )

    rol = models.CharField(max_length=20, choices=ROLES)

    # Vínculo con el registro audiovisual (puede ser null si aún no encontrado)
    persona_humana = models.ForeignKey(
        "registro_audiovisual.PersonaHumana",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participaciones_postulacion",
    )

    # Nombre que tipea el presentante para buscar al integrante
    nombre_busqueda = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre ingresado por el presentante para localizar al integrante en el registro.",
    )

    verificado = models.BooleanField(
        default=False,
        help_text="True cuando persona_humana fue encontrada y vinculada en el registro.",
    )

    class Meta:
        unique_together = ("postulacion", "rol")
        verbose_name = "Integrante del equipo"
        verbose_name_plural = "Integrantes del equipo"

    def __str__(self):
        nombre = self.persona_humana.nombre_completo if self.persona_humana else self.nombre_busqueda or "—"
        return f"{self.get_rol_display()} · {nombre}"


# ==========================================
# DOCUMENTOS DE INTEGRANTES DEL EQUIPO
# ==========================================
class DocumentoIntegrante(models.Model):
    """
    Documentación por integrante del equipo (DNI y constancia ARCA).
    Separada de DocumentoPostulacion para mantener la trazabilidad por persona.
    """

    TIPOS = [
        ("DNI",                "DNI anverso y reverso"),
        ("CONSTANCIA_ARCA",    "Constancia de inscripción en ARCA"),
        ("CV_BIOFILMOGRAFIA",  "CV / Biofilmografía"),
    ]

    ESTADOS = [
        ("PENDIENTE", "Pendiente de envío"),
        ("ENVIADO",   "Enviado"),
    ]

    integrante = models.ForeignKey(
        IntegrantePostulacion,
        on_delete=models.CASCADE,
        related_name="documentos",
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)

    archivo = models.FileField(
        upload_to="postulaciones/integrantes/",
        validators=[validar_documento_admitido, validar_tamano_archivo],
    )

    estado = models.CharField(max_length=10, choices=ESTADOS, default="PENDIENTE")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_envio  = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("integrante", "tipo")
        verbose_name = "Documento de integrante"
        verbose_name_plural = "Documentos de integrantes"

    def __str__(self):
        return f"{self.integrante} · {self.get_tipo_display()}"


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
    planilla_xlsx = models.FileField(
        upload_to="rendiciones/planillas/",
        blank=True, null=True,
        verbose_name="Planilla de rendición (.xlsx)",
    )
    observaciones_usuario = models.TextField(blank=True)
    observaciones_admin = models.TextField(blank=True)

    # Impacto económico — montos por categoría
    honorarios_tecnicos      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Honorarios técnicos")
    honorarios_elenco        = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Honorarios elenco")
    otros_honorarios         = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Otros honorarios")
    insumos                  = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Insumos")
    servicios_audiovisuales  = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Servicios audiovisuales")
    servicios_logistica      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Servicios / logística")

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


# ==========================================
# EVALUACIÓN DEL COMITÉ / JURADO
# ==========================================

class CriterioEvaluacion(models.Model):
    convocatoria    = models.ForeignKey(
        "Convocatoria",
        on_delete=models.CASCADE,
        related_name="criterios_evaluacion",
    )
    nombre          = models.CharField(max_length=200)
    puntaje_maximo  = models.PositiveIntegerField(default=10)
    orden           = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Criterio de evaluación"
        verbose_name_plural = "Criterios de evaluación"

    def __str__(self):
        return f"{self.nombre} (max {self.puntaje_maximo}) — {self.convocatoria.titulo}"


class EvaluacionPostulacion(models.Model):
    postulacion         = models.OneToOneField(
        "Postulacion",
        on_delete=models.CASCADE,
        related_name="evaluacion",
    )
    no_puntuar          = models.BooleanField(
        default=False,
        help_text="Marcar si el comité decide no evaluar este proyecto.",
    )
    fundamentacion      = models.TextField(
        blank=True,
        help_text="Fundamentación del comité sobre el proyecto.",
    )
    ultima_edicion_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="evaluaciones_cargadas",
    )
    fecha_modificacion  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluación de postulación"
        verbose_name_plural = "Evaluaciones de postulaciones"

    @property
    def puntaje_total(self):
        if self.no_puntuar:
            return None
        return sum(p.puntaje for p in self.puntajes.all() if p.puntaje is not None)

    def __str__(self):
        return f"Evaluación — {self.postulacion}"


class PuntajeCriterio(models.Model):
    evaluacion  = models.ForeignKey(
        EvaluacionPostulacion,
        on_delete=models.CASCADE,
        related_name="puntajes",
    )
    criterio    = models.ForeignKey(
        CriterioEvaluacion,
        on_delete=models.CASCADE,
        related_name="puntajes",
    )
    puntaje     = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("evaluacion", "criterio")
        verbose_name = "Puntaje por criterio"
        verbose_name_plural = "Puntajes por criterio"

    def clean(self):
        if self.puntaje is not None and self.puntaje > self.criterio.puntaje_maximo:
            raise ValidationError(
                f"El puntaje no puede superar el máximo de {self.criterio.puntaje_maximo}."
            )

    def __str__(self):
        return f"{self.criterio.nombre}: {self.puntaje}"


# ==========================================
# SEÑALES — limpieza de archivos al borrar
# ==========================================
@receiver(post_delete, sender=DocumentoPostulacion)
def borrar_archivo_documento_postulacion(sender, instance, **kwargs):
    if instance.archivo:
        instance.archivo.delete(save=False)


@receiver(post_delete, sender=DocumentoIntegrante)
def borrar_archivo_documento_integrante(sender, instance, **kwargs):
    if instance.archivo:
        instance.archivo.delete(save=False)