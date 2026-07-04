from django.db import migrations, models


def poblar_nombre_apellido(apps, schema_editor):
    """Divide nombre_completo en nombre + apellido para todos los registros existentes."""
    PersonaHumana = apps.get_model("registro_audiovisual", "PersonaHumana")
    for ph in PersonaHumana.objects.all():
        nc = (ph.nombre_completo or "").strip()
        partes = nc.split(" ", 1)
        ph.nombre = partes[0] if partes else ""
        ph.apellido = partes[1] if len(partes) > 1 else ""
        ph.save(update_fields=["nombre", "apellido"])


def revertir_nombre_apellido(apps, schema_editor):
    """Reconstruye nombre_completo desde nombre + apellido."""
    PersonaHumana = apps.get_model("registro_audiovisual", "PersonaHumana")
    for ph in PersonaHumana.objects.all():
        ph.nombre_completo = f"{ph.nombre} {ph.apellido}".strip()
        ph.save(update_fields=["nombre_completo"])


class Migration(migrations.Migration):

    dependencies = [
        ("registro_audiovisual", "0007_cuil_validator_area_desempeno_blank"),
    ]

    operations = [
        # ── PersonaHumana ──────────────────────────────────────────
        # 1. Agregar nombre y apellido con default temporal
        migrations.AddField(
            model_name="personahumana",
            name="nombre",
            field=models.CharField(default="", max_length=100, verbose_name="Nombre/s"),
        ),
        migrations.AddField(
            model_name="personahumana",
            name="apellido",
            field=models.CharField(default="", max_length=100, verbose_name="Apellido/s"),
        ),
        # 2. Poblar desde nombre_completo
        migrations.RunPython(poblar_nombre_apellido, revertir_nombre_apellido),
        # 3. Quitar campos denormalizados
        migrations.RemoveField(model_name="personahumana", name="nombre_completo"),
        migrations.RemoveField(model_name="personahumana", name="edad"),
        # 4. Agregar fecha_actualizacion
        migrations.AddField(
            model_name="personahumana",
            name="fecha_actualizacion",
            field=models.DateTimeField(auto_now=True),
        ),

        # ── PersonaJuridica ────────────────────────────────────────
        # 5. Quitar antigüedad denormalizada
        migrations.RemoveField(model_name="personajuridica", name="antiguedad"),
        # 6. Agregar fecha_actualizacion
        migrations.AddField(
            model_name="personajuridica",
            name="fecha_actualizacion",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
