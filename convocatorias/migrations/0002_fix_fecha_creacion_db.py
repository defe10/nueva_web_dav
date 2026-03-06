from django.db import migrations


def fix_fecha_creacion(apps, schema_editor):
    # Esta migración fue creada para SQLite (usa PRAGMA).
    # En PostgreSQL (y otros motores) se saltea.
    if schema_editor.connection.vendor != "sqlite":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(convocatorias_postulacion);")
        columns = [row[1] for row in cursor.fetchall()]  # nombre de columna

        # Si no existe la columna fecha_creacion, no hacemos nada
        if "fecha_creacion" not in columns:
            return

        # Si existe, aseguramos que no sea NULL (según tu lógica original)
        # Ajustá esto si tu migración original hacía otra cosa específica.
        cursor.execute("""
            UPDATE convocatorias_postulacion
            SET fecha_creacion = fecha
            WHERE fecha_creacion IS NULL;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("convocatorias", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fix_fecha_creacion, reverse_code=migrations.RunPython.noop),
    ]
