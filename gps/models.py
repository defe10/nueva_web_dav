from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# El vínculo con el registro solo puede apuntar a estos modelos.
_REGISTRO_LIMIT = {
    "app_label": "registro_audiovisual",
    "model__in": ("personahumana", "personajuridica"),
}


# ==========================================================
# OBRA  ─  entidad central del GPS / registro de obras
# ----------------------------------------------------------
# Agrupa el recorrido completo de un proyecto audiovisual:
#   · sus postulaciones (apoyo recibido vía la plataforma)
#   · su trayectoria de hitos (festivales, premios, etc.)
#   · (slice 2) su ficha técnica de registro de obra
#
# El dueño (owner) es el usuario postulante y mantiene los
# datos por autogestión. NO es un registro público.
# ==========================================================
class Obra(models.Model):

    ESTADOS_PRODUCCION = [
        ("desarrollo",     "En desarrollo"),
        ("produccion",     "En producción"),
        ("postproduccion", "En postproducción"),
        ("finalizada",     "Finalizada"),
    ]

    # Estado de seguimiento interno de la obra dentro del GPS.
    SEGUIMIENTO = [
        ("activa",        "Activa"),
        ("sin_novedades", "Sin novedades"),
        ("cerrado",       "Seguimiento cerrado"),
    ]

    # Tipo de obra, alineado con el "género" del modelo de Postulación.
    TIPOS_OBRA = [
        ("ficcion",    "Ficción"),
        ("documental", "Documental"),
        ("noficcion",  "No ficción"),
        ("educativo",  "Educativo"),
        ("deportivo",  "Deportivo"),
        ("simulacion", "Simulación"),
        ("ludico",     "Lúdico"),
        ("otro",       "Otro"),
    ]

    # Tipos alineados con el "Formato" del registro técnico de obra.
    FORMATOS = [
        ("cortometraje", "Cortometraje"),
        ("mediometraje", "Mediometraje"),
        ("largometraje", "Largometraje"),
        ("unitario",     "Unitario"),
        ("serie",        "Serie"),
        ("videoclip",    "Videoclip"),
        ("experimental", "Experimental"),
        ("videojuego",   "Videojuego"),
        ("otro",         "Otro"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="obras",
        verbose_name="Titular de la obra",
    )

    # Vínculo con el recorrido interno. Una obra puede agrupar N
    # postulaciones (fomento un año, otra convocatoria otro año) o
    # ninguna (obra sin apoyo, para la expansión futura).
    postulaciones = models.ManyToManyField(
        "convocatorias.Postulacion",
        related_name="obras",
        blank=True,
        verbose_name="Postulaciones vinculadas",
    )

    titulo = models.CharField(max_length=255)

    formato = models.CharField(max_length=20, choices=FORMATOS, blank=True)
    genero = models.CharField(
        "Tipo de obra", max_length=50, choices=TIPOS_OBRA, blank=True,
    )

    # Ventana temporal del proyecto (admite datos históricos). Opcionales
    # porque muchas obras están en desarrollo o con información incompleta.
    anio_inicio = models.PositiveSmallIntegerField(
        "Año de inicio", null=True, blank=True,
    )
    anio_finalizacion = models.PositiveSmallIntegerField(
        "Año de finalización", null=True, blank=True,
    )

    duracion = models.PositiveSmallIntegerField(
        "Duración (minutos)", null=True, blank=True,
        help_text="Duración estimada o definitiva, en minutos.",
    )

    # Dirección y Producción: texto libre + vínculo opcional al Registro
    # Audiovisual. Si el nombre coincide con un registro (PersonaHumana o
    # PersonaJuridica) se guarda el GenericForeignKey; si no, queda solo el texto.
    direccion = models.CharField(
        "Nombre/s y Apellido/s del Director/a", max_length=255, blank=True,
    )
    direccion_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", limit_choices_to=_REGISTRO_LIMIT,
    )
    direccion_object_id = models.PositiveIntegerField(null=True, blank=True)
    direccion_registro = GenericForeignKey(
        "direccion_content_type", "direccion_object_id",
    )

    produccion = models.CharField(
        "Nombre/s y Apellido/s del Productor/a", max_length=255, blank=True,
    )
    produccion_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", limit_choices_to=_REGISTRO_LIMIT,
    )
    produccion_object_id = models.PositiveIntegerField(null=True, blank=True)
    produccion_registro = GenericForeignKey(
        "produccion_content_type", "produccion_object_id",
    )

    sinopsis = models.TextField(blank=True)

    portada = models.ImageField(
        "Imagen / afiche / portada",
        upload_to="gps/portadas/", blank=True, null=True,
    )
    enlace = models.URLField(
        "Enlace del proyecto", blank=True,
        help_text="Tráiler, teaser o sitio del proyecto.",
    )

    estado_produccion = models.CharField(
        max_length=20, choices=ESTADOS_PRODUCCION, default="desarrollo",
    )

    seguimiento = models.CharField(
        max_length=20, choices=SEGUIMIENTO, default="activa",
    )

    # Flag opcional de control interno de la Secretaría. Los datos son
    # auto-declarados por el titular; el staff puede marcarlos verificados.
    verificado = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_actualizacion"]
        verbose_name = "Obra"
        verbose_name_plural = "Obras"

    def clean(self):
        super().clean()
        if (self.anio_inicio and self.anio_finalizacion
                and self.anio_finalizacion < self.anio_inicio):
            raise ValidationError(
                {"anio_finalizacion": "El año de finalización no puede ser anterior al de inicio."}
            )

    def save(self, *args, **kwargs):
        """Archiva el título viejo cuando la obra cambia de nombre.

        Un proyecto suele circular con un título de desarrollo y estrenarse con
        otro: guardar el anterior es lo que permite reconocer después que se
        trata de la misma obra. Va acá y no en la vista para cubrir también las
        ediciones hechas desde el /admin.
        """
        titulo_previo = None
        if self.pk:
            titulo_previo = (
                Obra.objects
                .filter(pk=self.pk)
                .values_list("titulo", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if titulo_previo and titulo_previo != self.titulo:
            self.titulos_anteriores.get_or_create(
                titulo=titulo_previo,
                defaults={"anio_hasta": timezone.now().year, "automatico": True},
            )
            # Si volvió a un nombre que ya había usado, deja de ser "anterior".
            self.titulos_anteriores.filter(titulo=self.titulo).delete()

    def __str__(self):
        return self.titulo or "(Obra sin título)"


# ==========================================================
# TÍTULO ANTERIOR  ─  la obra cambió de nombre
# ----------------------------------------------------------
# Una fila por nombre con el que la obra circuló antes. Se
# carga sola cuando el titular (o el staff) edita el título, y
# a mano para los nombres previos a la plataforma. Es lo que
# permite buscar por el título viejo y reconocer el proyecto.
# El nombre con el que se postuló no se guarda acá: eso ya vive
# congelado en `Postulacion.nombre_proyecto`.
# ==========================================================
class TituloAnterior(models.Model):

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="titulos_anteriores",
    )

    titulo = models.CharField("Título anterior", max_length=255)

    anio_hasta = models.PositiveSmallIntegerField(
        "Se llamó así hasta", null=True, blank=True,
    )

    nota = models.CharField(
        max_length=255, blank=True,
        help_text="P. ej. \"título de desarrollo\" o \"título de festival\".",
    )

    # Distingue lo que archivó el sistema al detectar el cambio de título de lo
    # que cargó una persona.
    automatico = models.BooleanField("Registrado automáticamente", default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-anio_hasta", "-id"]
        verbose_name = "Título anterior"
        verbose_name_plural = "Títulos anteriores"
        constraints = [
            models.UniqueConstraint(
                fields=["obra", "titulo"], name="gps_titulo_anterior_unico",
            ),
        ]

    def __str__(self):
        if self.anio_hasta:
            return f"{self.titulo} (hasta {self.anio_hasta})"
        return self.titulo


# ==========================================================
# HITO DE TRAYECTORIA  ─  sistema "+Hito"
# ----------------------------------------------------------
# Línea de tiempo unificada de la vida de la obra afuera de
# la plataforma. Una sola tabla con `tipo` + campos comunes
# de primer nivel (útiles para estadística) + `metadata`
# JSON para lo específico de cada tipo.
# ==========================================================
class Hito(models.Model):

    TIPOS = [
        ("apoyo",        "Otro apoyo"),
        ("premio",       "Premio / reconocimiento"),
        ("festival",     "Festival"),
        ("mercado",      "Mercado"),
        ("laboratorio",  "Laboratorio"),
        ("estreno",      "Estreno o exhibición"),
        ("distribucion", "Distribución o lanzamiento"),
    ]

    # Estado normalizado del hito, para estadística y filtros. Opcional:
    # no todos los tipos de hito requieren un estado. El campo `resultado`
    # (texto libre) sigue describiendo el resultado concreto.
    ESTADOS = [
        ("postulado",       "Postulado"),
        ("preseleccionado", "Preseleccionado"),
        ("seleccionado",    "Seleccionado"),
        ("participante",    "Participante"),
        ("nominado",        "Nominado"),
        ("ganador",         "Ganador"),
        ("no_seleccionado", "No seleccionado"),
        ("finalizado",      "Finalizado"),
    ]

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name="hitos",
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)

    estado = models.CharField(max_length=20, choices=ESTADOS, blank=True)

    nombre = models.CharField(
        "Nombre del evento / apoyo", max_length=255,
    )

    # Fecha exacta si se conoce; si no, alcanza con el año.
    anio = models.PositiveSmallIntegerField("Año")
    fecha = models.DateField(null=True, blank=True)

    pais = models.CharField("País", max_length=100, blank=True)
    lugar = models.CharField("Ciudad / lugar", max_length=150, blank=True)

    # Entidad otorgante / institución / fondo / festival organizador.
    entidad = models.CharField(max_length=255, blank=True)

    # Edición del evento (p. ej. "15ª edición").
    edicion = models.CharField(max_length=100, blank=True)

    # Resultado transversal: ganador/nominado/mención (premio),
    # competencia oficial/muestra/WIP (festival), etc.
    resultado = models.CharField(max_length=255, blank=True)

    # Monto de apoyos externos, para estadística de impacto.
    monto = models.DecimalField(
        "Monto", max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Solo si el hito implicó un monto (premio, apoyo, etc.).",
    )

    MONEDAS = [
        ("ARS", "Peso argentino (ARS)"),
        ("USD", "Dólar (USD)"),
        ("EUR", "Euro (EUR)"),
        ("BRL", "Real (BRL)"),
    ]
    moneda = models.CharField(max_length=10, choices=MONEDAS, blank=True)

    # Un premio suele salir dentro de un festival: se encadena con su hito.
    hito_origen = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="premios",
        verbose_name="Surge del hito",
        help_text="P. ej. el festival del que proviene este premio.",
    )

    descripcion = models.TextField(blank=True)
    link = models.URLField(blank=True)
    adjunto = models.FileField(
        upload_to="gps/hitos/", blank=True,
        help_text="Comprobante / constancia (opcional).",
    )

    # Campos específicos de cada tipo que no ameritan columna propia.
    metadata = models.JSONField(default=dict, blank=True)

    verificado = models.BooleanField(default=False)

    # Quién cargó el hito (titular o staff). SET_NULL para no perder el
    # hito si se elimina el usuario.
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="hitos_creados",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-anio", "-fecha"]
        verbose_name = "Hito de trayectoria"
        verbose_name_plural = "Hitos de trayectoria"

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.nombre} ({self.anio})"


# ==========================================================
# FICHA TÉCNICA  ─  registro técnico de la obra terminada
# ----------------------------------------------------------
# Fase final del recorrido: la obra depositada en el Archivo
# Histórico (equivalente al formulario "Registro Técnico de
# Obra Audiovisual"). Modelo aparte y OneToOne: es opcional
# (no toda obra llegó a esta etapa) y no infla la ficha
# básica de `Obra`. Solo campos técnicos/de registro que NO
# están ya en `Obra` (título, formato, sinopsis, dirección,
# producción, año, duración ya viven ahí).
# ==========================================================
class FichaTecnica(models.Model):

    RESOLUCIONES = [
        ("SD",      "SD"),
        ("HD",      "HD"),
        ("FULLHD",  "Full HD"),
        ("2K",      "2K"),
        ("4K",      "4K"),
        ("5K",      "5K"),
        ("otros",   "Otros"),
    ]

    RELACIONES_ASPECTO = [
        ("4:3",     "4:3"),
        ("16:9",    "16:9"),
        ("17:9",    "17:9"),
        ("1.85:1",  "1.85:1"),
        ("2.40:1",  "2.40:1"),
    ]

    MEDIOS_ENTREGA = [
        ("pen_drive",      "Pen drive"),
        ("memoria",        "Memoria externa"),
        ("transferencia",  "Transferencia virtual"),
    ]

    obra = models.OneToOneField(
        Obra,
        on_delete=models.CASCADE,
        related_name="ficha_tecnica",
    )

    # ── Créditos ──────────────────────────────────────────
    # Los créditos por cargo viven en CreditoFichaTecnica (una fila por
    # persona, con vínculo opcional al Registro Audiovisual).
    elenco = models.TextField("Elenco principal", blank=True)

    # ── Producción / localización ─────────────────────────
    pais = models.CharField("País de producción", max_length=120, blank=True)
    locaciones_rodaje = models.TextField("Locaciones de rodaje", blank=True)
    idioma = models.CharField(max_length=120, blank=True)
    detalle_financiamiento = models.TextField(
        "Detalle de financiamiento", blank=True,
        help_text="Instituciones, tipo de apoyo, año.",
    )

    # ── Especificaciones técnicas ─────────────────────────
    resolucion = models.CharField(max_length=10, choices=RESOLUCIONES, blank=True)
    relacion_aspecto = models.CharField(max_length=10, choices=RELACIONES_ASPECTO, blank=True)
    codec_especificaciones = models.TextField(
        "Codec / formato / especificaciones técnicas", blank=True,
    )
    caracteristicas_color = models.CharField(max_length=255, blank=True)
    caracteristicas_sonido = models.CharField(
        "Características de sonido", max_length=255, blank=True,
        help_text="Canales, sistema, etc.",
    )

    # ── Entrega / legal ───────────────────────────────────
    medio_entrega = models.CharField(max_length=20, choices=MEDIOS_ENTREGA, blank=True)
    copyright = models.TextField("Copyright / propiedad intelectual", blank=True)
    notas = models.TextField(
        "Notas", blank=True,
        help_text="Agradecimientos, auspicios, disponibilidad web, etc.",
    )

    # ── Material de archivo ───────────────────────────────
    usa_material_archivo = models.BooleanField(
        "¿Incluye imágenes de archivo?", null=True, blank=True,
    )
    origen_archivo = models.TextField(
        "Origen del material de archivo", blank=True,
        help_text="Estatal, privado, personal, televisión, prensa, etc.",
    )
    gestion_archivo = models.TextField(
        "Gestión del material de archivo", blank=True,
        help_text="Cómo se obtuvieron las copias y dónde se localizan.",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ficha técnica"
        verbose_name_plural = "Fichas técnicas"

    def __str__(self):
        return f"Ficha técnica · {self.obra.titulo}"


# ==========================================================
# CRÉDITO DE FICHA TÉCNICA  ─  una persona por fila
# ----------------------------------------------------------
# Cada cargo admite N personas. Igual que Dirección/Producción
# en Obra: el nombre es texto libre y, si coincide con alguien
# del Registro Audiovisual, se guarda además el vínculo.
# ==========================================================
class CreditoFichaTecnica(models.Model):

    CARGOS = [
        ("guionista",   "Guionista/s"),
        ("productor",   "Productor/a"),
        ("fotografia",  "Director/a de fotografía"),
        ("arte",        "Director/a de arte"),
        ("montaje",     "Montajista"),
        ("sonido",      "Director/a de sonido"),
        ("otro",        "Otro crédito"),
    ]

    ficha = models.ForeignKey(
        FichaTecnica,
        on_delete=models.CASCADE,
        related_name="creditos",
    )

    cargo = models.CharField(max_length=20, choices=CARGOS)

    # Solo para cargo "otro": qué rol cumple (edición, música, animación…).
    detalle = models.CharField(
        "Rol", max_length=150, blank=True,
        help_text="Solo para 'Otro crédito': especificá el rol.",
    )

    nombre = models.CharField("Nombre", max_length=255)
    nombre_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", limit_choices_to=_REGISTRO_LIMIT,
    )
    nombre_object_id = models.PositiveIntegerField(null=True, blank=True)
    nombre_registro = GenericForeignKey(
        "nombre_content_type", "nombre_object_id",
    )

    class Meta:
        ordering = ["cargo", "id"]
        verbose_name = "Crédito de ficha técnica"
        verbose_name_plural = "Créditos de ficha técnica"

    def __str__(self):
        rol = self.detalle if self.cargo == "otro" and self.detalle else self.get_cargo_display()
        return f"{rol}: {self.nombre}"
