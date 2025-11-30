from django.db import models
from django.contrib.auth.models import User
from datetime import date


# ---------- CHOICES COMUNES ----------

GENEROS = [
    ('MUJER', 'Mujer'),
    ('VARON', 'Varón'),
    ('NO_DICE', 'Prefiero no decirlo'),
    ('X', 'X'),
    ('OTRA', 'Mi género se ve representado por otra identidad'),
]

NIVEL_EDUCATIVO = [
    ('PRIMARIO', 'Primario completo'),
    ('SECUNDARIO', 'Secundario completo'),
    ('TERCIARIO', 'Terciario completo'),
    ('UNIVERSITARIO', 'Universitario completo'),
    ('POSGRADO', 'Posgrado completo'),
]

# Por ahora solo algunos lugares, vos completás después:
LUGARES_RESIDENCIA = [
    ('AGUARAY', 'Aguaray'),
    ('AGUAS_BLANCAS', 'Aguas Blancas'),
    ('OTRO', 'Otro'),
]

TIPO_PERSONA_JURIDICA = [
    ('EMPRESA', 'Empresa'),
    ('ASOC_CIVIL', 'Asociación civil'),
    ('FUNDACION', 'Fundación'),
    ('COOPERATIVA', 'Cooperativa de trabajo'),
    ('OTRA', 'Otra'),
]

# Áreas de desempeño: vos los completás después
AREAS_DESEMPENO = [
    ('PRODUCTOR', 'Productor/a'),
    ('JEFE_PRODUCCION', 'Jefe de producción'),
    # ...
]


# ---------- PERSONA HUMANA ----------

class PersonaHumana(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    nombre_completo = models.CharField(max_length=255)
    cuil_cuit = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    edad = models.PositiveIntegerField(blank=True, null=True)

    lugar_residencia = models.CharField(max_length=50, choices=LUGARES_RESIDENCIA)
    residencia_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Completar solo si seleccionaste 'Otro' en lugar de residencia."
    )

    domicilio_real = models.CharField(max_length=255)
    telefono_contacto = models.CharField(max_length=50)
    correo_electronico = models.EmailField()

    genero = models.CharField(max_length=20, choices=GENEROS)
    nivel_educativo = models.CharField(max_length=20, choices=NIVEL_EDUCATIVO)

    area_desempeno_1 = models.CharField(max_length=50, choices=AREAS_DESEMPENO)
    area_desempeno_2 = models.CharField(max_length=50, choices=AREAS_DESEMPENO, blank=True, null=True)
    area_desempeno_3 = models.CharField(max_length=50, choices=AREAS_DESEMPENO, blank=True, null=True)

    area_cultural_complementaria = models.CharField(max_length=255, blank=True, null=True)
    medios_experiencia = models.CharField(max_length=255, blank=True, null=True)
    links = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Persona humana: {self.nombre_completo}"

    def calcular_edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    def save(self, *args, **kwargs):
        # si no se cargó edad, o queremos recalcular siempre:
        self.edad = self.calcular_edad()
        super().save(*args, **kwargs)


# ---------- PERSONA JURÍDICA ----------

class PersonaJuridica(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    razon_social = models.CharField(max_length=255)
    nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    tipo_persona_juridica = models.CharField(max_length=20, choices=TIPO_PERSONA_JURIDICA)

    # Por ahora un solo set de choices; después podemos hacer lógica
    area_desempeno_1 = models.CharField(max_length=50)
    area_desempeno_2 = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Persona jurídica: {self.razon_social}"


