from django.db import migrations, connection

def fix_fecha_creacion(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(convocatorias_postulacion);")
        cols = [row[1] for row in cursor.fetchall()]

    if "fecha_creacion" not in cols:
        schema_editor.execute(
            "ALTER TABLE convocatorias_postulacion ADD COLUMN fecha_creacion datetime;"
        )
        # Completar existentes para que no queden null
        schema_editor.execute(
            "UPDATE convocatorias_postulacion "
            "SET fecha_creacion = COALESCE(fecha_envio, CURRENT_TIMESTAMP) "
            "WHERE fecha_creacion IS NULL;"
        )

class Migration(migrations.Migration):

    dependencies = [
        ("convocatorias", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fix_fecha_creacion, migrations.RunPython.noop),
    ]
