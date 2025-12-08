from django.db import models
from django.contrib.auth.models import User


LUGARES_RESIDENCIA = [
    ('', '- Seleccionar -'),
    ('SC', 'Salta Capital'),
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
    ('GP', 'General Pizzarro'),
    ('GM', 'General Mosconi'),
    ('GB', 'General Ballivián'),
    ('Gu', 'Guachipas'),
    ('HI', 'Hipólito Yrigoyen'),
    ('Ir', 'Iruya'),
    ('IC', 'Isla de Cañas'),
    ('JVG', 'Joaquín V. Gonzalez'),
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
    ('SC', 'San Carlos'),
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
    ("otro", "Otro"),
]

SITUACION_IVA = [('', '- Seleccionar -'),
        ('N', 'Ninguna'),
        ('EX', 'Exento'),
        ('M', 'Monotributista'),
        ('RI', 'Responsable Inscripto'),
        ('O', 'Otra'),

]

ACTIVIDAD_DGR = [
    ('', '- Seleccionar -'),
    ('PF', '591110 - Producción de filmes y videocintas'),
    ('PPF', '591120 - Postproducción de filmes y videocintas'),
    ('O', 'Otra'),
    ('N', 'Ninguna'),

]

AREA_DESEMPENO_1 = [
        ('', '- Seleccionar -'),
        ('Productor', 'Productor/a'),
        ('Jefe_prod', 'Jefe/a de producción'),
        ('Asist_prod', 'Asistente de producción'),
        ('Jefe_loc', 'Jefe/a de locaciones'), #continuar
        ('Director', 'Director/a'),
        ('Asist_Dir', 'Asistente de dirección'),
        ('Dir_Cast', 'Director/a de casting'),
        ('Dir_Foto', 'Director/a de fotografía'),
        ('Camara', 'Camarógrafo/a'),
        ('Key_Grip', 'Key Grip'),
        ('Video Asist_DIT', 'Video Asist / DIT<'),
        ('Gaffer', 'Gaffer'),
        ('Guionista', 'Guionista'),
        ('Reflec', 'Reflectorista'),
        ('Dir_Arte', 'Dirección de Arte'),
        ('Escnog', 'Escenógrafo/a'),
        ('Vest', 'Vestuarista'),
        ('Maqui', 'Jefe/a de Maquillaje'),
        ('Dir_Son', 'Dirección de Sonido'),
        ('Ayu_Son', 'Ayudante de Sonido '),
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
        ('', '- Seleccionar -'),
        ('Productor', 'Productor/a'),
        ('Jefe_prod', 'Jefe/a de producción'),
        ('Asist_prod', 'Asistente de producción'),
        ('Jefe_loc', 'Jefe/a de locaciones'), #continuar
        ('Director', 'Director/a'),
        ('Asist_Dir', 'Asistente de dirección'),
        ('Dir_Cast', 'Director/a de casting'),
        ('Dir_Foto', 'Director/a de fotografía'),
        ('Camara', 'Camarógrafo/a'),
        ('Key_Grip', 'Key Grip'),
        ('Video Asist_DIT', 'Video Asist / DIT<'),
        ('Gaffer', 'Gaffer'),
        ('Guionista', 'Guionista'),
        ('Reflec', 'Reflectorista'),
        ('Dir_Arte', 'Dirección de Arte'),
        ('Escnog', 'Escenógrafo/a'),
        ('Vest', 'Vestuarista'),
        ('Maqui', 'Jefe/a de Maquillaje'),
        ('Dir_Son', 'Dirección de Sonido'),
        ('Ayu_Son', 'Ayudante de Sonido '),
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
        ('', '- Seleccionar -'),
        ('', '- Empresas -'),
        ('Productora', 'Empresa de producción'),
        ('PostProd', 'Empresa de postproducción'),
        ('Serv_Prod', 'Empresa de servicios para la producción'),
        ('', '- Personas Jurídicas s/fines de lucro -'),
        ('PPJJ_Espec', 'Específica Audiovisual '),
        ('PPJJ_Cult', 'Cultural'),
        ('otro', 'Otro'),
    ]

AREA_DESEMPENO_PPJJ_2 = [
        ('', '- Seleccionar -'),
        ('', '- Empresas -'),
        ('Productora', 'Empresa de producción'),
        ('PostProd', 'Empresa de postproducción'),
        ('Serv_Prod', 'Empresa de servicios para la producción'),
        ('', '- Personas Jurídicas s/fines de lucro -'),
        ('PPJJ_Espec', 'Específica Audiovisual '),
        ('PPJJ_Cult', 'Cultural'),
        ('otro', 'Otro'),
    ]

AREA_CULTURAL = [
        ('', '- Seleccionar -'),
        ('Actor', 'Actror / Actríz'),
        ('musica', 'Música'),
        ('danza', 'Danza'),
        ('literatura', 'Literatura'),
        ('visuales', 'Artes Visuales'),
        ('comunicacion', 'Comunicación'),
        ('locutor', 'Locutor/a'),
        ('educacion', 'Educación'),
        ('otro', 'Otro'),
    ]

# -------------------------------
# PERSONA HUMANA
# -------------------------------

class PersonaHumana(models.Model):
    nombre_completo = models.CharField(max_length=200)
    cuil_cuit = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=50, choices=[
        ('', '- Seleccionar -'),
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("NB", "No binario"),
        ("O", "Otro"),
    ])
    lugar_residencia = models.CharField(
    max_length=100,
    choices=LUGARES_RESIDENCIA,
    default="",
)
    otro_lugar_residencia = models.CharField(
    max_length=150,
    blank=True,
    null=True,
)
    nivel_educativo = models.CharField(max_length=50, choices=[
        ('', '- Seleccionar -'),
        ('Pc', 'Primario completo'),
        ('Sc', 'Secundario completo'),
        ('Tc', 'Terciario completo'),
        ('Uc', 'Universitario completo'),
        ('Pos', 'Posgrado completo'),
    ])
    domicilio_real = models.CharField(max_length=250)
    telefono = models.CharField(max_length=50)
    email = models.EmailField()

    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name="persona_humana",
    null=True,
    blank=True
)


    # Datos fiscales
    situacion_iva = models.CharField(
    max_length=100,
    choices=SITUACION_IVA,
    default="",
)
    actividad_dgr = models.CharField(
    max_length=100,
    choices=ACTIVIDAD_DGR,
    default="",
)
    domicilio_fiscal = models.CharField(max_length=250, blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)


    # Datos profesionales
    area_desempeno_1 = models.CharField(max_length=50, choices=AREA_DESEMPENO_1, verbose_name="Área de desempeño 1")
    area_desempeno_2 = models.CharField(max_length=50, choices=AREA_DESEMPENO_2, verbose_name="Área de desempeño 2")
    area_cultural = models.CharField(max_length=50, choices=AREA_CULTURAL, verbose_name="Área cultural complementaria")
    link_1 = models.CharField(max_length=250)
    link_2 = models.CharField(max_length=250, blank=True, null=True)
    link_3 = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.nombre_completo


# -------------------------------
# PERSONA JURÍDICA
# -------------------------------

class PersonaJuridica(models.Model):
    tipo_persona_juridica = models.CharField(max_length=100, choices=[
        ("asociacion", "Asociación Civil"),
        ("fundacion", "Fundación"),
        ("empresa", "Empresa"),
        ("cooperativa", "Cooperativa"),
    ])
    cuil_cuit = models.CharField(max_length=20)
    razon_social = models.CharField(max_length=200)
    nombre_comercial = models.CharField(max_length=200, blank=True, null=True)

    domicilio_fiscal = models.CharField(max_length=250)
    lugar_residencia = models.CharField(
    max_length=100,
    choices=LUGARES_RESIDENCIA,
    default="",
)
    otro_lugar_residencia = models.CharField(
    max_length=150,
    blank=True,
    null=True,
)

    # Fecha de constitución (antes usabas fecha_nacimiento)
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


    # Datos fiscales
    situacion_iva = models.CharField(
    max_length=100,
    choices=SITUACION_IVA,
    default="",
)
    actividad_dgr = models.CharField(
    max_length=100,
    choices=ACTIVIDAD_DGR,
    default="",
)
    fecha_creacion = models.DateTimeField(auto_now_add=True)


    # Datos profesionales
    area_desempeno_JJPP_1 = models.CharField(max_length=50, choices=AREA_DESEMPENO_PPJJ_1, verbose_name="Área de desempeño PPJJ 1")
    area_desempeno_JJPP_2 = models.CharField(max_length=50, choices=AREA_DESEMPENO_PPJJ_2, verbose_name="Área de desempeño PPJJ 2")
    link_1 = models.CharField(max_length=250)
    link_2 = models.CharField(max_length=250)
    link_3 = models.CharField(max_length=250)



    def __str__(self):
        return self.razon_social
