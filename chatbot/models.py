from django.db import models


class Nodo(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    mensaje = models.TextField()
    es_inicio = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    nodo_origen = models.ForeignKey(
        Nodo,
        related_name="opciones",
        on_delete=models.CASCADE
    )
    texto = models.CharField(max_length=200)
    nodo_destino = models.ForeignKey(
        Nodo,
        on_delete=models.CASCADE
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]

    def __str__(self):
        return f"{self.texto} -> {self.nodo_destino.nombre}"


class PalabraClave(models.Model):
    texto = models.CharField(max_length=100, unique=True)
    nodo_destino = models.ForeignKey(
        Nodo,
        on_delete=models.CASCADE,
        related_name="palabras_clave"
    )
    activo = models.BooleanField(default=True)
    prioridad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Palabra clave"
        verbose_name_plural = "Palabras clave"
        ordering = ["-prioridad", "texto"]

    def __str__(self):
        return f"{self.texto} ({self.prioridad})"