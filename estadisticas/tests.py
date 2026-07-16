from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from convocatorias.models import Convocatoria, Postulacion, Rendicion
from registro_audiovisual.models import PersonaHumana

from estadisticas.views.comun import conteo, filas_barras, normalizar_localidad, pct, rango
from estadisticas.views.impacto import impacto, montos_comparados
from estadisticas.views.postulaciones import agrupar, postulaciones_qs, tasas
from estadisticas.views.registro import _residencia


def crear_convocatoria(titulo="Convocatoria test"):
    return Convocatoria.objects.create(
        titulo=titulo,
        slug=titulo.lower().replace(" ", "-"),
        categoria="CONCURSO",
        linea="fomento",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
    )


def crear_persona(user, genero="F", lugar="SC", otro=None, nacimiento=date(1990, 5, 1)):
    return PersonaHumana.objects.create(
        user=user,
        nombre="Nombre",
        apellido=user.username,
        cuil_cuit="20123456789",
        fecha_nacimiento=nacimiento,
        genero=genero,
        nivel_educativo="Uc",
        lugar_residencia=lugar,
        otro_lugar_residencia=otro,
        domicilio_real="Calle 123",
        codigo_postal_real="4400",
        telefono="387000000",
        email=f"{user.username}@test.com",
        area_desempeno_1="Director",
        area_cultural="ninguna",
    )


def crear_postulacion(user, conv, estado="enviado", **kwargs):
    return Postulacion.objects.create(
        user=user,
        convocatoria=conv,
        estado=estado,
        fecha_envio="2026-03-01T12:00:00Z",
        **kwargs,
    )


class PersonasUnicasTest(TestCase):
    """Los indicadores demográficos cuentan presentantes únicos,
    no una vez por postulación."""

    def setUp(self):
        self.conv = crear_convocatoria()
        self.ana = User.objects.create(username="ana")
        self.beto = User.objects.create(username="beto")
        crear_persona(self.ana, genero="F")
        crear_persona(self.beto, genero="M")
        # Ana presenta DOS proyectos; Beto uno.
        crear_postulacion(self.ana, self.conv)
        crear_postulacion(self.ana, self.conv)
        crear_postulacion(self.beto, self.conv)

    def test_demograficos_no_repiten_personas(self):
        datos = agrupar(postulaciones_qs({}))
        self.assertEqual(datos["presentantes_unicos"], 2)
        self.assertEqual(dict(datos["genero_persona"]), {"Femenino": 1, "Masculino": 1})

    def test_postulaciones_si_cuentan_por_proyecto(self):
        datos = agrupar(postulaciones_qs({}))
        self.assertEqual(datos["por_conv"][0]["total"], 3)

    def test_borradores_excluidos(self):
        crear_postulacion(self.beto, crear_convocatoria("Otra"), estado="borrador")
        self.assertEqual(postulaciones_qs({}).count(), 3)


class GanadoresTest(TestCase):
    def test_solo_ganadores_filtra_seleccionado_y_finalizado(self):
        conv = crear_convocatoria()
        user = User.objects.create(username="ana")
        crear_postulacion(user, conv, estado="seleccionado")
        crear_postulacion(user, conv, estado="finalizado")
        crear_postulacion(user, conv, estado="enviado")
        crear_postulacion(user, conv, estado="no_seleccionado")
        self.assertEqual(postulaciones_qs({"solo_ganadores": True}).count(), 2)


class ImpactoTest(TestCase):
    def setUp(self):
        self.conv = crear_convocatoria()
        self.user = User.objects.create(username="ana")

    def _rendicion(self, estado="APROBADO", fecha_aprobacion=None, **montos):
        p = crear_postulacion(self.user, self.conv, estado="finalizado")
        return Rendicion.objects.create(
            postulacion=p, user=self.user, estado=estado,
            fecha_aprobacion=fecha_aprobacion, **montos,
        )

    def test_suma_decimal_exacta(self):
        self._rendicion(honorarios_tecnicos=Decimal("1000.10"),
                        honorarios_tecnicos_cantidad=3,
                        fecha_aprobacion=date(2026, 4, 1))
        self._rendicion(honorarios_tecnicos=Decimal("0.20"),
                        honorarios_tecnicos_cantidad=2,
                        fecha_aprobacion=date(2026, 5, 1))
        imp = impacto({})
        self.assertEqual(imp["impacto_total"], Decimal("1000.30"))
        self.assertIsInstance(imp["impacto_total"], Decimal)
        fila = imp["impacto_filas"][0]
        self.assertEqual(fila["monto"], Decimal("1000.30"))
        self.assertEqual(fila["cantidad"], 5)

    def test_solo_rendiciones_aprobadas(self):
        self._rendicion(estado="ENVIADO", honorarios_tecnicos=Decimal("999"))
        imp = impacto({})
        self.assertEqual(imp["impacto_count"], 0)
        self.assertEqual(imp["impacto_total"], Decimal("0"))

    def test_filtro_por_anio_de_aprobacion(self):
        self._rendicion(honorarios_tecnicos=Decimal("100"),
                        fecha_aprobacion=date(2025, 12, 20))
        self._rendicion(honorarios_tecnicos=Decimal("50"),
                        fecha_aprobacion=date(2026, 1, 10))
        imp = impacto({"anio": "2026"})
        self.assertEqual(imp["impacto_count"], 1)
        self.assertEqual(imp["impacto_total"], Decimal("50"))


class LocalidadOtroTest(TestCase):
    def test_normalizacion_unifica_variantes(self):
        self.assertEqual(normalizar_localidad(" san  pedro "), "San Pedro")
        self.assertEqual(normalizar_localidad("SAN PEDRO"), "San Pedro")
        self.assertEqual(normalizar_localidad(None), "")

    def test_residencia_desagrega_otro(self):
        u1 = User.objects.create(username="u1")
        u2 = User.objects.create(username="u2")
        u3 = User.objects.create(username="u3")
        crear_persona(u1, lugar="otro", otro="san pedro ")
        crear_persona(u2, lugar="otro", otro="SAN PEDRO")
        crear_persona(u3, lugar="SC")
        filas = {f["label"]: f["total"] for f in _residencia(PersonaHumana.objects.all())}
        self.assertEqual(filas["San Pedro"], 2)
        self.assertEqual(filas["Salta Capital"], 1)
        self.assertNotIn("Otro", filas)


class TasasTest(TestCase):
    def test_tasas_del_embudo(self):
        conv = crear_convocatoria()
        user = User.objects.create(username="ana")
        crear_postulacion(user, conv, estado="enviado")
        crear_postulacion(user, conv, estado="no_admitido")
        crear_postulacion(user, conv, estado="admitido")
        p_sel = crear_postulacion(user, conv, estado="seleccionado")
        crear_postulacion(user, conv, estado="finalizado")
        Rendicion.objects.create(postulacion=p_sel, user=user, estado="APROBADO")

        resultado = {t["nombre"]: t for t in tasas(postulaciones_qs({}))["tasas"]}
        # 3 de 5 superaron la admisión (admitido, seleccionado, finalizado)
        self.assertEqual(resultado["Admisión"]["valor"], 60.0)
        # 2 de 5 ganadoras
        self.assertEqual(resultado["Selección"]["valor"], 40.0)
        # 1 finalizada de 2 ganadoras
        self.assertEqual(resultado["Finalización"]["valor"], 50.0)
        # 1 rendición aprobada de 2 ganadoras
        self.assertEqual(resultado["Rendición aprobada"]["valor"], 50.0)

    def test_tasas_sin_base_devuelven_none(self):
        resultado = {t["nombre"]: t for t in tasas(postulaciones_qs({}))["tasas"]}
        self.assertIsNone(resultado["Admisión"]["valor"])
        self.assertIsNone(resultado["Finalización"]["valor"])


class MontosComparadosTest(TestCase):
    def setUp(self):
        self.conv = crear_convocatoria()
        self.user = User.objects.create(username="ana")

    def test_otorgado_rendido_aprobado_y_ejecucion(self):
        p1 = crear_postulacion(self.user, self.conv, estado="seleccionado",
                               monto_otorgado=Decimal("1000"))
        p2 = crear_postulacion(self.user, self.conv, estado="finalizado",
                               monto_otorgado=Decimal("500"))
        # Rendición aprobada por 600 y otra solo enviada por 300
        Rendicion.objects.create(postulacion=p1, user=self.user, estado="APROBADO",
                                 insumos=Decimal("600"),
                                 fecha_aprobacion=date(2026, 5, 1))
        Rendicion.objects.create(postulacion=p2, user=self.user, estado="ENVIADO",
                                 insumos=Decimal("300"))

        m = montos_comparados({})
        self.assertEqual(m["monto_otorgado"], Decimal("1500"))
        self.assertEqual(m["monto_rendido"], Decimal("900"))
        self.assertEqual(m["monto_aprobado"], Decimal("600"))
        self.assertEqual(m["pct_ejecucion"], 40.0)
        self.assertEqual(m["ganadoras_sin_monto"], 0)

    def test_avisa_ganadoras_sin_monto_cargado(self):
        crear_postulacion(self.user, self.conv, estado="seleccionado")
        m = montos_comparados({})
        self.assertEqual(m["ganadoras_sin_monto"], 1)
        self.assertIsNone(m["pct_ejecucion"])


class ExportacionesTest(TestCase):
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def setUp(self):
        staff = User.objects.create(username="staff", is_staff=True)
        self.client.force_login(staff)

    def test_exportaciones_responden_xlsx(self):
        for url in ["/estadisticas/exportar/",
                    "/estadisticas/registro/exportar/",
                    "/estadisticas/exenciones/exportar/",
                    "/estadisticas/formacion/exportar/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertEqual(r["Content-Type"], self.XLSX, url)


class HelpersTest(TestCase):
    def test_rango_etario(self):
        self.assertEqual(rango(17), "Menos de 18")
        self.assertEqual(rango(30), "18-30")
        self.assertEqual(rango(51), "51 o más")
        self.assertEqual(rango(None), "Sin dato")

    def test_conteo_mapea_labels(self):
        u = User.objects.create(username="u1")
        crear_persona(u, genero="NB")
        filas = conteo(PersonaHumana.objects.all(), "genero", {"NB": "No binario"})
        self.assertEqual(filas, [{"label": "No binario", "total": 1}])

    def test_pct(self):
        self.assertEqual(pct(1, 3), 33.3)
        self.assertIsNone(pct(1, 0))

    def test_filas_barras_calcula_maximo_y_pesos(self):
        datos = filas_barras([(2025, 10), (2026, 25)])
        self.assertEqual(datos["max_total"], 25)
        self.assertEqual(datos["filas"][0]["display"], 10)
        datos = filas_barras([(2026, Decimal("1234567.89"))], con_pesos=True)
        self.assertEqual(datos["filas"][0]["display"], "$1.234.567")
