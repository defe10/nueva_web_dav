from django.db import models
from django.contrib.auth.models import User


# ----- CHOICES -----

LINEAS_FOMENTO = [
    ('CONC_FICCION', 'Concurso de cortometrajes de ficción'),
    ('CONC_VIDEOCLIP', 'Concurso de videoclips'),
    ('PROG_LARGOS', 'Desarrollo de largometrajes'),
    ('PROG_LAB_CORTOS', 'Laboratorio de cortometrajes'),
    ('PROG_COMUNIDAD', 'Cine en comunidad'),
    ('PROG_ANIMACION', 'Entrenamiento en animación'),
    ('PROG_VIDEOJUEGOS', 'Desarrollo de videojuegos'),
    ('SUB_RODAJE', 'Apoyo a rodaje'),
    ('SUB_FINALIZACION', 'Apoyo a finalización de obras'),
    ('SUB_EVENTOS', 'Apoyo a participación en eventos audiovisuales'),
]

TIPOS_PROYECTO = [
    ('CORTO', 'Cortometraje'),
    ('LARGO', 'Largometraje'),
    ('VIDEOCLIP', 'Videoclip'),
    ('TRANSMEDIA', 'Transmedia'),
    ('SERIE', 'Serie'),
    ('VIDEOJUEGO', 'Videojuego'),
    ('ANIMACION', 'Animación'),
    ('COMUNIDAD', 'Cine en comunidad'),
]

GENEROS = [
    ('FICCION', 'Ficción'),
    ('DOCUMENTAL', 'Documental'),
    ('NO_FICCION', 'No ficción'),
    ('EDUCATIVO', 'Educativo'),
    ('DEPORTIVO', 'Deportivo'),
    ('LUDICO', 'Lúdico'),
    ('SIMULACION', 'Simulación'),
    ('OTRO', 'Otro'),
]


# ----- MODELO PRINCIPAL -----

class PostulacionIDEA(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    linea_fomento = models.CharField(max_length=50, choices=LINEAS_FOMENTO)
    nombre_proyecto = models.CharField(max_length=255)
    tipo_proyecto = models.CharField(max_length=50, choices=TIPOS_PROYECTO)
    genero = models.CharField(max_length=50, choices=GENEROS)
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

