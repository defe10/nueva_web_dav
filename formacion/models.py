from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from convocatorias.validators import validar_documento_admitido, validar_tamano_archivo


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
    ("",                 "- Seleccionar -"),
    ("masculino",        "Masculino"),
    ("femenino",         "Femenino"),
    ("no_binario",       "No binario"),
    ("otro",             "Otro"),
    ("prefiero_no_decir","Prefiero no decirlo"),
]

ESTADOS = [
    ("inscripto", "Inscripto"),
    ("admitido", "Admitido"),
    ("no_admitido", "No admitido"),
    ("lista_espera", "Lista de espera"),
]


class InscripcionFormacion(models.Model):
    """
    Inscripción a una convocatoria de línea "formacion".
    No requiere Registro Audiovisual obligatorio.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    convocatoria = models.ForeignKey(
        "convocatorias.Convocatoria",
        on_delete=models.CASCADE,
    )

    persona_humana = models.ForeignKey(
        PersonaHumana, on_delete=models.SET_NULL, null=True, blank=True
    )
    persona_juridica = models.ForeignKey(
        PersonaJuridica, on_delete=models.SET_NULL, null=True, blank=True
    )

    nombre = models.CharField(max_length=120, blank=True)
    apellido = models.CharField(max_length=120, blank=True)
    dni = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=60, blank=True)

    localidad = models.CharField(max_length=20, choices=LOCALIDADES, blank=True)
    otra_localidad = models.CharField(max_length=120, blank=True)

    vinculo_sector = models.CharField(max_length=20, choices=VINCULO_SECTOR, blank=True)

    genero = models.CharField(max_length=20, choices=GENERO, blank=True)
    edad   = models.PositiveSmallIntegerField(null=True, blank=True)

    documentacion = models.FileField(
        upload_to="formacion/documentacion/",
        blank=True,
        null=True,
        validators=[validar_documento_admitido, validar_tamano_archivo],
        verbose_name="Documentación",
    )

    declaracion_jurada = models.BooleanField(default=False)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="inscripto")

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "convocatoria")
        ordering = ["-fecha"]
        verbose_name = "Inscripción a formación"
        verbose_name_plural = "Inscripciones a formación"

    def clean(self):
        super().clean()

        if not self.convocatoria_id:
            return

        if self.convocatoria.linea != "formacion":
            raise ValidationError(
                "Esta inscripción solo corresponde a convocatorias de línea Formación."
            )

        if self.persona_humana_id and self.persona_juridica_id:
            raise ValidationError(
                "La inscripción no puede vincular Persona Humana y Persona Jurídica al mismo tiempo."
            )

        tiene_registro = bool(self.persona_humana_id or self.persona_juridica_id)
        if not tiene_registro:
            if not self.email:
                raise ValidationError({"email": "Ingresá un email de contacto."})
            if not self.telefono:
                raise ValidationError({"telefono": "Ingresá un teléfono de contacto."})

        if self.localidad == "otro" and not self.otra_localidad.strip():
            raise ValidationError({"otra_localidad": "Indicá tu localidad."})

    def __str__(self):
        titulo = self.convocatoria.titulo if self.convocatoria_id else "(sin convocatoria)"
        return f"{self.user.username} → {titulo} ({self.estado})"


# ==========================================
# CONFIGURACIÓN DE INSCRIPCIÓN FORMACIÓN
# ==========================================
class ConfiguracionInscripcionFormacion(models.Model):
    """
    Define qué campos son visibles en el formulario de inscripción
    de una convocatoria de formación.
    """
    convocatoria = models.OneToOneField(
        "convocatorias.Convocatoria",
        on_delete=models.CASCADE,
        related_name="config_inscripcion_formacion",
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
