from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exencion", "0003_add_tipo_to_exencion_documento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="exencion",
            name="estado",
            field=models.CharField(
                choices=[
                    ("BORRADOR", "Borrador"),
                    ("ENVIADA", "Enviada"),
                    ("OBSERVADA", "Observada — requiere subsanación"),
                    ("APROBADA", "Aprobada"),
                    ("RECHAZADA", "Rechazada"),
                ],
                default="BORRADOR",
                max_length=20,
            ),
        ),
    ]
