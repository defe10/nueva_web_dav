from django.db import models
from django.contrib.auth.models import User


LUGARES_RESIDENCIA = [
    ('SC', 'Salta Capital'),
    ('otro', 'Otro'),
    ('Ag', 'Aguaray'),
    ('AB', 'Aguas Blancas'),
    ('An', 'Angastaco'),
    ('Ai', 'Animaná'),
    ('AS', 'Apolinario Saravia'),
    ('Ca', 'Cachi'),
    ('Cf', 'Cafayate'),
    ('CQ', 'Campo Quijano'),
    ('CS', 'Campo Santo'),
    ('Ce', 'Cerrillos'),
    ('Ch', 'Chicoana'),
    ('CSR', 'Colonia Santa Rosa'),
    ('CM', 'Coronel Moldes'),
    ('EB', 'El Bordo'),
    ('EC', 'El Carril'),
    ('EG', 'El Galpón'),
    ('EJ', 'El Jardín'),
    ('EP', 'El Potrero'),
    ('EQ', 'El Quebrachal'),
    ('ET', 'El Tala'),
    ('Em', 'Embarcación'),
    ('GG', 'General Güemes'),
    ('GP', 'General Pizarro'),
    ('GM', 'General Mosconi'),
    ('GB', 'General Ballivián'),
    ('Gu', 'Guachipas'),
    ('HI', 'Hipólito Yrigoyen'),
    ('Ir', 'Iruya'),
    ('IC', 'Isla de Cañas'),
    ('JVG', 'Joaquín V. González'),
    ('LC', 'La Caldera'),
    ('LCa', 'La Candelaria'),
    ('LM', 'La Merced'),
    ('LP', 'La Poma'),
    ('LV', 'La Viña'),
    ('LL', 'Las Lajitas'),
    ('LT', 'Los Toldos'),
    ('Mo', 'Molinos'),
    ('Na', 'Nazareno'),
    ('Pa', 'Payogasta'),
    ('PSM', 'Profesor Salvador Mazza'),
    ('RP', 'Río Piedras'),
    ('RBN', 'Rivadavia Banda Norte'),
    ('RBS', 'Rivadavia Banda Sur'),
    ('SAC', 'San Antonio de los Cobres'),
    ('SCa', 'San Carlos'),
    ('SJM', 'San José de Metán'),
    ('SL', 'San Lorenzo'),
    ('Or', 'San Ramón de la Nueva Orán'),
    ('SVE', 'Santa Victoria Este'),
    ('SVO', 'Santa Victoria Oeste'),
    ('Se', 'Seclantás'),
    ('Ta', 'Tartagal'),
    ('TG', 'Tolar Grande'),
    ('Ur', 'Urundel'),
    ('Va', 'Vaqueros'),
]

SITUACION_IVA = [
    ('N', 'Ninguna'),
    ('EX', 'Exento'),
    ('M', 'Monotributista'),
    ('RI', 'Responsable Inscripto'),
    ('O', 'Otra'),
]

ACTIVIDAD_DGR = [
    ('591110', '591110 - Producción de filmes y videocintas'),
    ('591120', '591120 - Postproducción de filmes y videocintas'),
    ('O', 'Otra'),
    ('N', 'Ninguna'),
]

AREA_DESEMPENO_1 = [
    ('Productor', 'Productor/a'),
    ('Jefe_prod', 'Jefe/a de producción'),
    ('Asist_prod', 'Asistente de producción'),
    ('Jefe_loc', 'Jefe/a de locaciones'),
    ('Director', 'Director/a'),
    ('Asist_Dir', 'Asistente de dirección'),
    ('Dir_Cast', 'Director/a de casting'),
    ('Dir_Foto', 'Director/a de fotografía'),
    ('Camara', 'Camarógrafo/a'),
    ('Key_Grip', 'Key Grip'),
    ('Video_Asist_DIT', 'Video Asist / DIT'),
    ('Gaffer', 'Gaffer'),
    ('Guionista', 'Guionista'),
    ('Reflec', 'Reflectorista'),
    ('Dir_Arte', 'Dirección de Arte'),
    ('Escnog', 'Escenógrafo/a'),
    ('Vest', 'Vestuarista'),
    ('Maqui', 'Jefe/a de Maquillaje'),
    ('Dir_Son', 'Dirección de Sonido'),
    ('Ayu_Son', 'Ayudante de Sonido'),
    ('Dir_Son_Post', 'Dirección de Sonido Post / Mezclador/a'),
    ('Post_Prod', 'Postproductor/a'),
    ('Editor', 'Editor/a'),
    ('Color', 'Colorista'),
    ('Animam', 'Animador/a'),
    ('Realizador', 'Realizador/a integral'),
    ('Game_Design', 'Game Designer'),
    ('Game_Artist', 'Game Artist'),
    ('otro', 'Otro'),
]

AREA_DESEMPENO_2 = [
    ('Productor', 'Productor/a'),
    ('Jefe_prod', 'Jefe/a de producción'),
    ('Asist_prod', 'Asistente de producción'),
    ('Jefe_loc', 'Jefe/a de locaciones'),
    ('Director', 'Director/a'),
    ('Asist_Dir', 'Asistente de dirección'),
    ('Dir_Cast', 'Director/a de casting'),
    ('Dir_Foto', 'Director/a de fotografía'),
    ('Camara', 'Camarógrafo/a'),
    ('Key_Grip', 'Key Grip'),
    ('Video_Asist_DIT', 'Video Asist / DIT'),
    ('Gaffer', 'Gaffer'),
    ('Guionista', 'Guionista'),
    ('Reflec', 'Reflectorista'),
    ('Dir_Arte', 'Dirección de Arte'),
    ('Escnog', 'Escenógrafo/a'),
    ('Vest', 'Vestuarista'),
    ('Maqui', 'Jefe/a de Maquillaje'),
    ('Dir_Son', 'Dirección de Sonido'),
    ('Ayu_Son', 'Ayudante de Sonido'),
    ('Dir_Son_Post', 'Dirección de Sonido Post / Mezclador/a'),
    ('Post_Prod', 'Postproductor/a'),
    ('Editor', 'Editor/a'),
    ('Color', 'Colorista'),
    ('Animam', 'Animador/a'),
    ('Realizador', 'Realizador/a integral'),
    ('Game_Design', 'Game Designer'),
    ('Game_Artist', 'Game Artist'),
    ('otro', 'Otro'),
]

AREA_DESEMPENO_PPJJ_1 = [
    ('Productora', 'Empresa de producción'),
    ('PostProd', 'Empresa de postproducción'),
    ('Serv_Prod', 'Empresa de servicios para la producción'),
    ('PPJJ_Espec', 'Persona jurídica específica audiovisual'),
    ('PPJJ_Cult', 'Persona jurídica cultural'),
    ('otro', 'Otro'),
]

AREA_DESEMPENO_PPJJ_2 = [
    ('Productora', 'Empresa de producción'),
    ('PostProd', 'Empresa de postproducción'),
    ('Serv_Prod', 'Empresa de servicios para la producción'),
    ('PPJJ_Espec', 'Persona jurídica específica audiovisual'),
    ('PPJJ_Cult', 'Persona jurídica cultural'),
    ('otro', 'Otro'),
]

AREA_CULTURAL = [
    ('Actor', 'Actor / Actriz'),
    ('musica', 'Música'),
    ('danza', 'Danza'),
    ('literatura', 'Literatura'),
    ('visuales', 'Artes Visuales'),
    ('comunicacion', 'Comunicación'),
    ('locutor', 'Locutor/a'),
    ('educacion', 'Educación'),
    ('ninguna', 'Ninguna'),
    ('otro', 'Otro'),
]

GENERO_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('NB', 'No binario'),
    ('O', 'Otro'),
]

NIVEL_EDUCATIVO_CHOICES = [
    ('Pc', 'Primario completo'),
    ('Sc', 'Secundario completo'),
    ('Tc', 'Terciario completo'),
    ('Uc', 'Universitario completo'),
    ('Pos', 'Posgrado completo'),
]

TIPO_PERSONA_JURIDICA_CHOICES = [
    ('asociacion', 'Asociación Civil'),
    ('fundacion', 'Fundación'),
    ('empresa', 'Empresa'),
    ('cooperativa', 'Cooperativa'),
]


# -------------------------------
# PERSONA HUMANA
# -------------------------------

class PersonaHumana(models.Model):
    nombre_completo = models.CharField(max_length=200)
    cuil_cuit = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    edad = models.PositiveIntegerField()

    genero = models.CharField(
        max_length=10,
        choices=GENERO_CHOICES
    )

    nivel_educativo = models.CharField(
        max_length=50,
        choices=NIVEL_EDUCATIVO_CHOICES,
        verbose_name="Nivel educativo alcanzado"
    )

    lugar_residencia = models.CharField(
        max_length=100,
        choices=LUGARES_RESIDENCIA
    )

    otro_lugar_residencia = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    domicilio_real = models.CharField(max_length=250)
    codigo_postal_real = models.CharField(max_length=10)

    telefono = models.CharField(max_length=50)
    email = models.EmailField()

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="persona_humana",
        null=True,
        blank=True
    )

    situacion_iva = models.CharField(
        max_length=5,
        choices=SITUACION_IVA,
        blank=True,
        null=True
    )

    actividad_dgr = models.CharField(
        max_length=10,
        choices=ACTIVIDAD_DGR,
        blank=True,
        null=True
    )

    domicilio_fiscal = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    codigo_postal_fiscal = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    localidad_fiscal = models.CharField(
        max_length=100,
        choices=LUGARES_RESIDENCIA,
        blank=True,
        null=True
    )

    area_desempeno_1 = models.CharField(
        max_length=50,
        choices=AREA_DESEMPENO_1,
        verbose_name="Área de desempeño principal"
    )

    area_desempeno_2 = models.CharField(
        max_length=50,
        choices=AREA_DESEMPENO_2,
        blank=True,
        null=True,
        verbose_name="Área de desempeño secundaria"
    )

    area_cultural = models.CharField(
        max_length=50,
        choices=AREA_CULTURAL,
        verbose_name="Área cultural complementaria"
    )

    portfolio_web = models.CharField(
        "Sitio web / Portfolio",
        max_length=300,
        blank=True,
        default="",
        help_text="Sitio web personal, de la productora o portfolio online (Vimeo, Behance, etc.)"
    )

    canal_video = models.CharField(
        "Canal audiovisual",
        max_length=300,
        blank=True,
        default="",
        help_text="Canal de YouTube, Vimeo u otra plataforma de video"
    )

    instagram = models.CharField(
        "Instagram",
        max_length=300,
        blank=True,
        default="",
        help_text="Perfil de Instagram profesional"
    )

    linkedin = models.CharField(
        "LinkedIn",
        max_length=300,
        blank=True,
        default="",
        help_text="Perfil de LinkedIn"
    )

    link_trabajo_destacado = models.CharField(
        "Trabajo destacado",
        max_length=300,
        blank=True,
        default="",
        help_text="Link a una obra o trabajo audiovisual relevante"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo


# -------------------------------
# PERSONA JURÍDICA
# -------------------------------

class PersonaJuridica(models.Model):
    tipo_persona_juridica = models.CharField(
        max_length=100,
        choices=TIPO_PERSONA_JURIDICA_CHOICES
    )

    cuil_cuit = models.CharField(max_length=20)
    razon_social = models.CharField(max_length=200)
    nombre_comercial = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    domicilio_fiscal = models.CharField(max_length=250)

    localidad_fiscal = models.CharField(
        max_length=100,
        choices=LUGARES_RESIDENCIA
    )

    codigo_postal_fiscal = models.CharField(max_length=10)

    situacion_iva = models.CharField(
        max_length=5,
        choices=SITUACION_IVA
    )

    actividad_dgr = models.CharField(
        max_length=10,
        choices=ACTIVIDAD_DGR
    )

    fecha_constitucion = models.DateField()
    antiguedad = models.PositiveIntegerField()

    telefono = models.CharField(max_length=50)
    email = models.EmailField()

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="persona_juridica",
        null=True,
        blank=True
    )

    area_desempeno_JJPP_1 = models.CharField(
        max_length=50,
        choices=AREA_DESEMPENO_PPJJ_1,
        verbose_name="Área de desempeño principal"
    )

    area_desempeno_JJPP_2 = models.CharField(
        max_length=50,
        choices=AREA_DESEMPENO_PPJJ_2,
        verbose_name="Área de desempeño secundaria"
    )

    portfolio_web = models.CharField(
        "Sitio web / Portfolio",
        max_length=300,
        blank=True,
        default="",
        help_text="Sitio web personal, de la productora o portfolio online (Vimeo, Behance, etc.)"
    )

    canal_video = models.CharField(
        "Canal audiovisual",
        max_length=300,
        blank=True,
        default="",
        help_text="Canal de YouTube, Vimeo u otra plataforma de video"
    )

    instagram = models.CharField(
        "Instagram",
        max_length=300,
        blank=True,
        default="",
        help_text="Perfil de Instagram profesional"
    )

    linkedin = models.CharField(
        "LinkedIn",
        max_length=300,
        blank=True,
        default="",
        help_text="Perfil de LinkedIn"
    )

    link_trabajo_destacado = models.CharField(
        "Trabajo destacado",
        max_length=300,
        blank=True,
        default="",
        help_text="Link a una obra o trabajo audiovisual relevante"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.razon_social