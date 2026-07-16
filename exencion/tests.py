import os
import shutil
import tempfile
from datetime import date, timedelta
from io import StringIO

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exencion import depuracion
from exencion.models import Exencion, ExencionDocumento

MEDIA_TEST = tempfile.mkdtemp(prefix="test_exencion_")


def crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1, con_constancia=True,
                   con_documento=True, user=None):
    """Crea una exención con archivos. vencimiento_offset_dias<0 => vencida."""
    hoy = date.today()
    ex = Exencion.objects.create(
        user=user or User.objects.create(username=f"u{Exencion.objects.count()}"),
        nombre_razon_social="Juana Pérez",
        email="juana@test.com",
        cuit="27123456789",
        domicilio_fiscal="Calle 1",
        localidad_fiscal="SC",
        codigo_postal_fiscal="4400",
        actividad_dgr="591110",
        estado=estado,
        fecha_emision=hoy - timedelta(days=365) if estado == "APROBADA" else None,
        fecha_vencimiento=hoy + timedelta(days=vencimiento_offset_dias) if estado == "APROBADA" else None,
    )
    if con_constancia:
        ex.certificado_pdf.save("const.pdf", SimpleUploadedFile("const.pdf", b"%PDF- const"), save=True)
    if con_documento:
        ExencionDocumento.objects.create(
            exencion=ex, tipo="DNI",
            archivo=SimpleUploadedFile("dni.pdf", b"%PDF- dni"),
        )
    return ex


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class SenalesLimpiezaTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def test_borrar_documento_borra_archivo(self):
        ex = crear_exencion()
        doc = ex.documentos.first()
        ruta = doc.archivo.path
        self.assertTrue(os.path.exists(ruta))
        doc.delete()
        self.assertFalse(os.path.exists(ruta))

    def test_borrar_exencion_borra_constancia_y_documentos(self):
        ex = crear_exencion()
        const = ex.certificado_pdf.path
        doc = ex.documentos.first().archivo.path
        ex.delete()
        self.assertFalse(os.path.exists(const), "la constancia no debe quedar huérfana")
        self.assertFalse(os.path.exists(doc), "el documento no debe quedar huérfano")

    def test_regenerar_reemplaza_constancia_sin_dejar_huerfano(self):
        ex = crear_exencion()
        vieja = ex.certificado_pdf.path
        ex.regenerar_pdf()
        nueva = ex.certificado_pdf.path
        self.assertNotEqual(vieja, nueva)
        self.assertFalse(os.path.exists(vieja), "la constancia vieja debe borrarse")
        self.assertTrue(os.path.exists(nueva))


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class DepuracionLogicaTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def test_depurables_solo_vencidas_o_rechazadas(self):
        vencida = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        vigente = crear_exencion(estado="APROBADA", vencimiento_offset_dias=+30)
        rechazada = crear_exencion(estado="RECHAZADA", con_constancia=False)
        en_tramite = crear_exencion(estado="ENVIADA", con_constancia=False)

        pks = set(depuracion.exenciones_depurables().values_list("pk", flat=True))
        self.assertIn(vencida.pk, pks)
        self.assertIn(rechazada.pk, pks)
        self.assertNotIn(vigente.pk, pks)
        self.assertNotIn(en_tramite.pk, pks)

    def test_ejecutar_borra_archivos_conserva_fila_y_marca(self):
        ex = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        const = ex.certificado_pdf.path
        doc = ex.documentos.first().archivo.path

        depuracion.ejecutar(depuracion.exenciones_depurables())

        self.assertFalse(os.path.exists(const))
        self.assertFalse(os.path.exists(doc))
        ex.refresh_from_db()
        self.assertTrue(Exencion.objects.filter(pk=ex.pk).exists(), "la fila se conserva")
        self.assertIsNotNone(ex.documentacion_depurada)
        self.assertFalse(ex.certificado_pdf, "el campo constancia queda vacío")
        self.assertEqual(ex.documentos.count(), 0)

    def test_solo_documentos_conserva_constancia(self):
        ex = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        const = ex.certificado_pdf.path
        depuracion.ejecutar(depuracion.exenciones_depurables(), incluir_constancia=False)
        self.assertTrue(os.path.exists(const), "la constancia se conserva con --solo-documentos")
        ex.refresh_from_db()
        self.assertEqual(ex.documentos.count(), 0)

    def test_no_reprocesa_depuradas(self):
        crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        depuracion.ejecutar(depuracion.exenciones_depurables())
        self.assertEqual(depuracion.exenciones_depurables().count(), 0)


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class ComandoTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def _run(self, *args):
        out = StringIO()
        call_command("depurar_exenciones", *args, stdout=out)
        return out.getvalue()

    def test_simulacion_no_borra(self):
        ex = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        doc = ex.documentos.first().archivo.path
        salida = self._run()
        self.assertIn("SIMULACIÓN", salida)
        self.assertTrue(os.path.exists(doc))

    def test_ejecutar_borra(self):
        ex = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        doc = ex.documentos.first().archivo.path
        self._run("--ejecutar")
        self.assertFalse(os.path.exists(doc))
        ex.refresh_from_db()
        self.assertIsNotNone(ex.documentacion_depurada)


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class AdminExencionTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.URL = reverse("admin:exencion_exencion_changelist")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@test.com", "x")
        self.vencida = crear_exencion(estado="APROBADA", vencimiento_offset_dias=-1)
        self.vigente = crear_exencion(estado="APROBADA", vencimiento_offset_dias=+30)

    def _post(self, pks, extra=None):
        data = {
            "action": "depurar_documentacion_action",
            "_selected_action": [str(p) for p in pks],
            "index": "0",
        }
        data.update(extra or {})
        return self.client.post(self.URL, data)

    def test_confirmacion_no_borra(self):
        self.client.force_login(self.superuser)
        r = self._post([self.vencida.pk, self.vigente.pk])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "borrar definitivamente")
        self.assertEqual(self.vencida.documentos.count(), 1)

    def test_confirmar_borra_solo_vencida(self):
        self.client.force_login(self.superuser)
        r = self._post([self.vencida.pk, self.vigente.pk], {"confirmar_depuracion": "1"})
        self.assertEqual(r.status_code, 302)
        self.vencida.refresh_from_db()
        self.vigente.refresh_from_db()
        self.assertIsNotNone(self.vencida.documentacion_depurada)
        self.assertIsNone(self.vigente.documentacion_depurada, "la vigente queda protegida")
        self.assertEqual(self.vencida.documentos.count(), 0)
        self.assertEqual(self.vigente.documentos.count(), 1)

    def test_staff_comun_no_tiene_accion_depurar(self):
        staff = User.objects.create(username="staff", is_staff=True)
        staff.user_permissions.set(
            Permission.objects.filter(content_type__app_label="exencion")
        )
        self.client.force_login(staff)
        r = self._post([self.vencida.pk], {"confirmar_depuracion": "1"})
        self.vencida.refresh_from_db()
        self.assertIsNone(self.vencida.documentacion_depurada)
        self.assertEqual(self.vencida.documentos.count(), 1)

    def test_filtro_oculta_archivadas_por_defecto(self):
        depuracion.ejecutar(Exencion.objects.filter(pk=self.vencida.pk))
        self.client.force_login(self.superuser)
        r = self.client.get(self.URL)
        ids = [e.pk for e in r.context["cl"].result_list]
        self.assertIn(self.vigente.pk, ids)
        self.assertNotIn(self.vencida.pk, ids, "la archivada no aparece por defecto")

        r2 = self.client.get(self.URL + "?archivada=archivadas")
        ids2 = [e.pk for e in r2.context["cl"].result_list]
        self.assertIn(self.vencida.pk, ids2)
