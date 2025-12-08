from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil"  # facilita user.perfil
    )
    telefono = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea automáticamente un PerfilUsuario asociado cuando se crea un User.
    """
    if created:
        PerfilUsuario.objects.create(user=instance)
