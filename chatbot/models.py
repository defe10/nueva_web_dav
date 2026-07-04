import unicodedata

from django.db import models
from django.core.exceptions import ValidationError


def _normalizar(texto):
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    return t.encode("ascii", "ignore").decode("utf-8")


# ============================================================
# NODO
# ============================================================
class Nodo(models.Model):
    nombre   = models.CharField(max_length=100)
    slug     = models.SlugField(unique=True)
    mensaje  = models.TextField()
    es_inicio = models.BooleanField(default=False)
    activo   = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def clean(self):
        # A: solo puede haber 1 nodo de inicio activo
        if self.es_inicio and self.activo:
            qs = Nodo.objects.filter(es_inicio=True, activo=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                otro = qs.first()
                raise ValidationError(
                    f"Ya existe un nodo de inicio activo: «{otro.nombre}». "
                    "Desactivalo o quitale la marca de inicio primero."
                )


# ============================================================
# OPCION
# ============================================================
class Opcion(models.Model):
    nodo_origen  = models.ForeignKey(Nodo, related_name="opciones", on_delete=models.CASCADE)
    texto        = models.CharField(max_length=200)
    nodo_destino = models.ForeignKey(Nodo, on_delete=models.CASCADE)
    orden        = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return f"{self.texto} -> {self.nodo_destino.nombre}"


# ============================================================
# PALABRA CLAVE
# ============================================================
class PalabraClave(models.Model):
    texto        = models.CharField(max_length=100, unique=True)
    nodo_destino = models.ForeignKey(Nodo, on_delete=models.CASCADE, related_name="palabras_clave")
    activo       = models.BooleanField(default=True)
    prioridad    = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Palabra clave"
        verbose_name_plural = "Palabras clave"
        ordering = ["-prioridad", "texto"]

    def __str__(self):
        return f"{self.texto} ({self.prioridad})"

    def save(self, *args, **kwargs):
        # E: normalizar al guardar para evitar duplicados lógicos
        self.texto = _normalizar(self.texto)
        super().save(*args, **kwargs)


# ============================================================
# CONFIGURACIÓN GLOBAL (singleton)
# ============================================================
class ConfiguracionChatbot(models.Model):
    mensaje_no_encontrado = models.TextField(
        default=(
            "No estoy seguro de haber entendido. "
            "Podés reformular la consulta o elegir una de las opciones disponibles."
        ),
        verbose_name="Mensaje cuando no se encuentra respuesta",
        help_text="Se muestra cuando ninguna palabra clave coincide con la consulta del usuario.",
    )

    class Meta:
        verbose_name = "Configuración del chatbot"
        verbose_name_plural = "Configuración del chatbot"

    def __str__(self):
        return "Configuración del chatbot"

    def clean(self):
        # D: singleton — solo puede existir una instancia
        qs = ConfiguracionChatbot.objects.exclude(pk=self.pk) if self.pk else ConfiguracionChatbot.objects.all()
        if qs.exists():
            raise ValidationError(
                "Solo puede existir una configuración del chatbot. Editá la existente."
            )

    @classmethod
    def get(cls):
        return cls.objects.first()


# ============================================================
# LOG DE CONSULTAS
# ============================================================
class ConsultaLog(models.Model):
    texto_consulta    = models.CharField(max_length=500)
    keyword_matcheada = models.CharField(max_length=100, blank=True, null=True)
    nodo_destino      = models.ForeignKey(
        Nodo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="consultas_log",
    )
    encontrado        = models.BooleanField(default=False)
    fecha             = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Consulta registrada"
        verbose_name_plural = "Consultas registradas"

    def __str__(self):
        ok = "✓" if self.encontrado else "✗"
        return f"{ok} «{self.texto_consulta[:50]}» — {self.fecha:%d/%m/%Y %H:%M}"
