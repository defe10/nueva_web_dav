"""
Crea datos de prueba para chequeo manual del sistema:
  1. usuario_humano  → PersonaHumana
  2. usuario_juridico → PersonaJuridica
  3. usuario_jurado  → grupo "jurado"
  4. Convocatoria fomento/concurso (vigente)
  5. Convocatoria formación sin registro (vigente)
  6. Convocatoria exención impositiva (vigente)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone

from registro_audiovisual.models import PersonaHumana, PersonaJuridica
from convocatorias.models import Convocatoria, ConfiguracionPostulacion


PASSWORD = "prueba1234"


class Command(BaseCommand):
    help = "Crea usuarios y convocatorias de prueba"

    def handle(self, *args, **options):
        self._crear_usuario_humano()
        self._crear_usuario_juridico()
        self._crear_usuario_jurado()
        self._crear_convocatoria_fomento()
        self._crear_convocatoria_formacion()
        self._crear_convocatoria_exencion()

        self.stdout.write(self.style.SUCCESS("\n✅ Datos de prueba creados correctamente.\n"))
        self.stdout.write("Credenciales de acceso (password: prueba1234):")
        self.stdout.write("  • usuario_humano   / prueba1234  → persona humana")
        self.stdout.write("  • usuario_juridico / prueba1234  → persona jurídica")
        self.stdout.write("  • usuario_jurado   / prueba1234  → grupo jurado")

    # ------------------------------------------------------------------ #
    # 1. PERSONA HUMANA                                                    #
    # ------------------------------------------------------------------ #
    def _crear_usuario_humano(self):
        user, created = User.objects.get_or_create(
            username="usuario_humano",
            defaults={
                "first_name": "Ana",
                "last_name": "García",
                "email": "ana.garcia.prueba@example.com",
            },
        )
        if created:
            user.set_password(PASSWORD)
            user.save()

        PersonaHumana.objects.get_or_create(
            user=user,
            defaults={
                "nombre_completo": "Ana García",
                "cuil_cuit": "27-30123456-4",
                "fecha_nacimiento": "1990-05-15",
                "edad": 35,
                "genero": "F",
                "nivel_educativo": "universitario_completo",
                "lugar_residencia": "SC",
                "domicilio_real": "Av. San Martín 450, Salta Capital",
                "codigo_postal_real": "4400",
                "telefono": "3874123456",
                "email": "ana.garcia.prueba@example.com",
                "situacion_iva": "M",
                "actividad_dgr": "591110",
                "domicilio_fiscal": "Av. San Martín 450",
                "codigo_postal_fiscal": "4400",
                "localidad_fiscal": "SC",
                "area_desempeno_1": "Productor",
                "area_desempeno_2": "Director",
                "area_cultural": "audiovisual",
            },
        )
        status = "creado" if created else "ya existía"
        self.stdout.write(f"  👤 usuario_humano {status}")

    # ------------------------------------------------------------------ #
    # 2. PERSONA JURÍDICA                                                  #
    # ------------------------------------------------------------------ #
    def _crear_usuario_juridico(self):
        user, created = User.objects.get_or_create(
            username="usuario_juridico",
            defaults={
                "first_name": "ProductoraSalta",
                "last_name": "SRL",
                "email": "productora.prueba@example.com",
            },
        )
        if created:
            user.set_password(PASSWORD)
            user.save()

        PersonaJuridica.objects.get_or_create(
            user=user,
            defaults={
                "tipo_persona_juridica": "SRL",
                "cuil_cuit": "30-70987654-1",
                "razon_social": "ProductoraSalta S.R.L.",
                "nombre_comercial": "ProductoraSalta",
                "domicilio_fiscal": "Caseros 1200, Salta Capital",
                "localidad_fiscal": "SC",
                "codigo_postal_fiscal": "4400",
                "situacion_iva": "RI",
                "actividad_dgr": "591110",
                "fecha_constitucion": "2015-03-20",
                "antiguedad": 10,
                "telefono": "3874999888",
                "email": "productora.prueba@example.com",
                "representante_nombre": "Carlos",
                "representante_apellido": "Mendoza",
                "representante_dni": "25678901",
                "area_desempeno_JJPP_1": "Productora",
                "area_desempeno_JJPP_2": "PostProd",
            },
        )
        status = "creado" if created else "ya existía"
        self.stdout.write(f"  🏢 usuario_juridico {status}")

    # ------------------------------------------------------------------ #
    # 3. JURADO                                                            #
    # ------------------------------------------------------------------ #
    def _crear_usuario_jurado(self):
        grupo_jurado, _ = Group.objects.get_or_create(name="jurado")

        user, created = User.objects.get_or_create(
            username="usuario_jurado",
            defaults={
                "first_name": "Roberto",
                "last_name": "Villalba",
                "email": "roberto.jurado.prueba@example.com",
            },
        )
        if created:
            user.set_password(PASSWORD)
            user.save()

        user.groups.add(grupo_jurado)
        status = "creado" if created else "ya existía"
        self.stdout.write(f"  ⚖️  usuario_jurado {status} (grupo: jurado)")

    # ------------------------------------------------------------------ #
    # 4. CONVOCATORIA FOMENTO / CONCURSO                                  #
    # ------------------------------------------------------------------ #
    def _crear_convocatoria_fomento(self):
        hoy = timezone.localdate()
        conv, created = Convocatoria.objects.get_or_create(
            slug="prueba-fomento-concurso",
            defaults={
                "titulo": "[PRUEBA] Concurso de Fomento Audiovisual",
                "descripcion_corta": "Convocatoria de prueba para concurso de fomento.",
                "descripcion_larga": (
                    "Esta convocatoria es exclusivamente para testing del sistema. "
                    "Los proyectos seleccionados recibirán financiamiento para producción audiovisual."
                ),
                "categoria": "CONCURSO",
                "linea": "fomento",
                "fecha_inicio": hoy,
                "fecha_fin": hoy.replace(year=hoy.year + 1),
                "bloque_personas": "JURADO",
                "orden": 99,
            },
        )
        if created:
            ConfiguracionPostulacion.objects.get_or_create(
                convocatoria=conv,
                defaults={
                    "tipo_postulante": "AMBAS",
                    "requiere_director": True,
                    "director_puede_coincidir": True,
                    "requiere_cbu": True,
                    "mostrar_titulo": True,
                    "mostrar_formato": True,
                    "mostrar_genero": True,
                    "requiere_sinopsis": True,
                    "mostrar_dossier": True,
                },
            )
        status = "creada" if created else "ya existía"
        self.stdout.write(f"  📋 Convocatoria fomento/concurso {status}")

    # ------------------------------------------------------------------ #
    # 5. CONVOCATORIA FORMACIÓN SIN REGISTRO                              #
    # ------------------------------------------------------------------ #
    def _crear_convocatoria_formacion(self):
        hoy = timezone.localdate()
        conv, created = Convocatoria.objects.get_or_create(
            slug="prueba-formacion-sin-registro",
            defaults={
                "titulo": "[PRUEBA] Taller de Guion — Inscripción libre",
                "descripcion_corta": "Convocatoria de prueba: formación sin registro audiovisual.",
                "descripcion_larga": (
                    "Taller intensivo de guion cinematográfico. "
                    "Inscripción abierta sin necesidad de registro en el sistema audiovisual."
                ),
                "categoria": "CURSO",
                "linea": "formacion",
                "tipo_formacion": "INSCRIPCION_LIBRE",
                "fecha_inicio": hoy,
                "fecha_fin": hoy.replace(year=hoy.year + 1),
                "bloque_personas": "TUTORES",
                "orden": 99,
            },
        )
        status = "creada" if created else "ya existía"
        self.stdout.write(f"  🎓 Convocatoria formación sin registro {status}")

    # ------------------------------------------------------------------ #
    # 6. CONVOCATORIA EXENCIÓN IMPOSITIVA                                 #
    # ------------------------------------------------------------------ #
    def _crear_convocatoria_exencion(self):
        hoy = timezone.localdate()
        conv, created = Convocatoria.objects.get_or_create(
            slug="prueba-exencion-impositiva",
            defaults={
                "titulo": "[PRUEBA] Exención Impositiva — Actividad Audiovisual",
                "descripcion_corta": "Convocatoria de prueba para exención impositiva.",
                "descripcion_larga": (
                    "Beneficio impositivo para personas físicas y jurídicas "
                    "que desarrollan actividad audiovisual en la provincia de Salta."
                ),
                "categoria": "BENEFICIO",
                "linea": "exencion",
                "fecha_inicio": hoy,
                "fecha_fin": hoy.replace(year=hoy.year + 1),
                "bloque_personas": "NINGUNO",
                "orden": 99,
            },
        )
        status = "creada" if created else "ya existía"
        self.stdout.write(f"  🧾 Convocatoria exención impositiva {status}")
