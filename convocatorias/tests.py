import os
import shutil
import tempfile
from datetime import date, timedelta
from io import StringIO

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from convocatorias.models import (
    Convocatoria, Postulacion, DocumentoPostulacion,
    IntegrantePostulacion, DocumentoIntegrante, Rendicion,
)

MEDIA_TEST = tempfile.mkdtemp(prefix="test_depuracion_")


def crear_convocatoria(titulo="Conv cerrada", cerrada=True):
    hoy = date.today()
    return Convocatoria.objects.create(
        titulo=titulo,
        slug=titulo.lower().replace(" ", "-"),
        categoria="CONCURSO",
        linea="fomento",
        fecha_inicio=hoy - timedelta(days=60),
        fecha_fin=hoy - timedelta(days=1) if cerrada else hoy + timedelta(days=30),
    )


def crear_postulacion_con_docs(user, conv, estado="no_seleccionado"):
    p = Postulacion.objects.create(user=user, convocatoria=conv, estado=estado)
    DocumentoPostulacion.objects.create(
        postulacion=p, tipo="GUION",
        archivo=SimpleUploadedFile("guion.pdf", b"%PDF- guion"),
    )
    integrante = IntegrantePostulacion.objects.create(postulacion=p, rol="DIRECTOR")
    DocumentoIntegrante.objects.create(
        integrante=integrante, tipo="DNI",
        archivo=SimpleUploadedFile("dni.pdf", b"%PDF- dni"),
    )
    return p


def depurar(*args):
    out = StringIO()
    call_command("depurar_documentacion", *args, stdout=out)
    return out.getvalue()


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class DepurarDocumentacionTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create(username="ana")
        self.conv = crear_convocatoria()

    def _docs_de(self, p):
        return (DocumentoPostulacion.objects.filter(postulacion=p).count()
                + DocumentoIntegrante.objects.filter(integrante__postulacion=p).count())

    def test_simulacion_no_borra_nada(self):
        p = crear_postulacion_con_docs(self.user, self.conv)
        salida = depurar()
        self.assertIn("SIMULACIÓN", salida)
        self.assertEqual(self._docs_de(p), 2)
        p.refresh_from_db()
        self.assertIsNone(p.documentacion_depurada)

    def test_ejecutar_borra_no_ganadoras_y_marca(self):
        p = crear_postulacion_con_docs(self.user, self.conv)
        archivo_fisico = DocumentoPostulacion.objects.get(postulacion=p).archivo.path
        self.assertTrue(os.path.exists(archivo_fisico))

        depurar("--ejecutar")

        self.assertEqual(self._docs_de(p), 0)
        self.assertFalse(os.path.exists(archivo_fisico), "el archivo físico debe borrarse")
        p.refresh_from_db()
        self.assertIsNotNone(p.documentacion_depurada)
        # Los datos de la postulación se conservan
        self.assertTrue(Postulacion.objects.filter(pk=p.pk).exists())

    def test_ganadoras_protegidas_por_defecto(self):
        ganadora = crear_postulacion_con_docs(self.user, self.conv, estado="seleccionado")
        finalizada = crear_postulacion_con_docs(self.user, self.conv, estado="finalizado")
        perdedora = crear_postulacion_con_docs(self.user, self.conv, estado="no_seleccionado")

        salida = depurar("--ejecutar")

        self.assertEqual(self._docs_de(ganadora), 2)
        self.assertEqual(self._docs_de(finalizada), 2)
        self.assertEqual(self._docs_de(perdedora), 0)
        self.assertIn("Protegidas: 2", salida)

    def test_incluir_ganadores_las_alcanza(self):
        ganadora = crear_postulacion_con_docs(self.user, self.conv, estado="seleccionado")
        depurar("--ejecutar", "--incluir-ganadores")
        self.assertEqual(self._docs_de(ganadora), 0)

    def test_convocatoria_abierta_intocable(self):
        abierta = crear_convocatoria("Conv abierta", cerrada=False)
        p = crear_postulacion_con_docs(self.user, abierta)
        depurar("--ejecutar")
        self.assertEqual(self._docs_de(p), 2)

    def test_tipos_borra_parcial_y_no_marca(self):
        p = crear_postulacion_con_docs(self.user, self.conv)
        depurar("--ejecutar", "--tipos", "DNI")
        # Se fue el DNI del integrante, queda el guion
        self.assertEqual(DocumentoIntegrante.objects.filter(integrante__postulacion=p).count(), 0)
        self.assertEqual(DocumentoPostulacion.objects.filter(postulacion=p).count(), 1)
        p.refresh_from_db()
        self.assertIsNone(p.documentacion_depurada, "con docs restantes no se marca depurada")

    def test_tipo_invalido_falla(self):
        with self.assertRaises(CommandError):
            depurar("--tipos", "NOEXISTE")

    def test_postulacion_ganadora_puntual_requiere_flag(self):
        ganadora = crear_postulacion_con_docs(self.user, self.conv, estado="seleccionado")
        with self.assertRaises(CommandError):
            depurar("--postulacion", str(ganadora.pk), "--ejecutar")
        self.assertEqual(self._docs_de(ganadora), 2)

    def test_filtro_por_convocatoria(self):
        otra = crear_convocatoria("Otra cerrada")
        p_dentro = crear_postulacion_con_docs(self.user, self.conv)
        p_fuera = crear_postulacion_con_docs(self.user, otra)
        depurar("--ejecutar", "--conv", str(self.conv.pk))
        self.assertEqual(self._docs_de(p_dentro), 0)
        self.assertEqual(self._docs_de(p_fuera), 2)

    def test_huerfanos_detecta_y_borra_solo_sin_referencia(self):
        p = crear_postulacion_con_docs(self.user, self.conv)
        referenciado = DocumentoPostulacion.objects.get(postulacion=p).archivo.path
        huerfano = os.path.join(MEDIA_TEST, "viejo_sin_registro.pdf")
        with open(huerfano, "wb") as f:
            f.write(b"%PDF- huerfano")

        salida = depurar("--huerfanos")
        self.assertIn("viejo_sin_registro.pdf", salida)
        self.assertTrue(os.path.exists(huerfano), "simulación no borra")

        depurar("--huerfanos", "--ejecutar")
        self.assertFalse(os.path.exists(huerfano))
        self.assertTrue(os.path.exists(referenciado), "los referenciados no se tocan")


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class DepurarDesdeAdminTest(TestCase):
    URL = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.URL = reverse("admin:convocatorias_convocatoria_changelist")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@test.com", "x")
        self.presentante = User.objects.create(username="ana")
        self.conv = crear_convocatoria()
        self.perdedora = crear_postulacion_con_docs(self.presentante, self.conv)
        self.ganadora = crear_postulacion_con_docs(self.presentante, self.conv, estado="seleccionado")

    def _docs_de(self, p):
        return (DocumentoPostulacion.objects.filter(postulacion=p).count()
                + DocumentoIntegrante.objects.filter(integrante__postulacion=p).count())

    def _post_accion(self, extra=None):
        data = {
            "action": "depurar_documentacion_action",
            "_selected_action": [str(self.conv.pk)],
            "index": "0",
        }
        data.update(extra or {})
        return self.client.post(self.URL, data)

    def test_muestra_confirmacion_sin_borrar(self):
        self.client.force_login(self.superuser)
        r = self._post_accion()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "borrar definitivamente")
        self.assertContains(r, "Ganadoras protegidas")
        self.assertEqual(self._docs_de(self.perdedora), 2, "la confirmación no borra nada")

    def test_confirmar_borra_no_ganadoras(self):
        self.client.force_login(self.superuser)
        r = self._post_accion({"confirmar_depuracion": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self._docs_de(self.perdedora), 0)
        self.assertEqual(self._docs_de(self.ganadora), 2, "ganadora protegida")
        self.perdedora.refresh_from_db()
        self.assertIsNotNone(self.perdedora.documentacion_depurada)

    def test_confirmar_incluyendo_ganadoras(self):
        self.client.force_login(self.superuser)
        self._post_accion({"confirmar_depuracion": "1", "incluir_ganadores": "1"})
        self.assertEqual(self._docs_de(self.perdedora), 0)
        self.assertEqual(self._docs_de(self.ganadora), 0)

    def test_staff_no_superusuario_no_tiene_la_accion(self):
        staff = User.objects.create(username="staff", is_staff=True)
        staff.user_permissions.set(
            Permission.objects.filter(content_type__app_label="convocatorias")
        )
        self.client.force_login(staff)
        r = self._post_accion({"confirmar_depuracion": "1"})
        # Django ignora la acción desconocida y no borra nada
        self.assertEqual(self._docs_de(self.perdedora), 2)
        self.assertEqual(self._docs_de(self.ganadora), 2)


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class BorradoIndividualEnAdminTest(TestCase):
    """Borrado de archivos uno por uno desde el detalle de la postulación."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@test.com", "x")
        self.presentante = User.objects.create(username="ana")
        self.conv = crear_convocatoria()
        self.post = crear_postulacion_con_docs(self.presentante, self.conv)
        self.url = reverse("admin:convocatorias_postulacion_change", args=[self.post.pk])

    def test_superusuario_ve_checkbox_de_eliminar(self):
        self.client.force_login(self.superuser)
        r = self.client.get(self.url)
        self.assertContains(r, "documentos-0-DELETE")

    def test_staff_comun_no_ve_checkbox_de_eliminar(self):
        staff = User.objects.create(username="staff", is_staff=True)
        staff.user_permissions.set(
            Permission.objects.filter(content_type__app_label="convocatorias")
        )
        self.client.force_login(staff)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "documentos-0-DELETE")

    def test_eliminar_un_archivo_borra_fila_y_archivo_fisico(self):
        doc = DocumentoPostulacion.objects.get(postulacion=self.post)
        archivo_fisico = doc.archivo.path
        self.assertTrue(os.path.exists(archivo_fisico))

        self.client.force_login(self.superuser)
        # GET para armar el POST del formulario con sus management forms
        r = self.client.get(self.url)
        form = r.context["adminform"].form
        data = {f.html_name: f.value() if f.value() is not None else "" for f in form}
        for formset in r.context["inline_admin_formsets"]:
            fs = formset.formset
            data[f"{fs.prefix}-TOTAL_FORMS"] = fs.total_form_count()
            data[f"{fs.prefix}-INITIAL_FORMS"] = fs.initial_form_count()
            data[f"{fs.prefix}-MIN_NUM_FORMS"] = 0
            data[f"{fs.prefix}-MAX_NUM_FORMS"] = 1000
            for f in fs.forms:
                for campo in f.fields:
                    if campo == "DELETE":
                        continue
                    valor = f[campo].value()
                    data[f"{f.prefix}-{campo}"] = "" if valor is None else valor

        # Marcar el documento del proyecto para eliminar
        data["documentos-0-DELETE"] = "on"
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 302, r.context["errors"] if r.status_code == 200 else "")

        self.assertFalse(DocumentoPostulacion.objects.filter(pk=doc.pk).exists())
        self.assertFalse(os.path.exists(archivo_fisico), "el archivo físico debe borrarse")
        # El resto de la postulación queda intacto
        self.assertTrue(Postulacion.objects.filter(pk=self.post.pk).exists())
        self.assertEqual(
            DocumentoIntegrante.objects.filter(integrante__postulacion=self.post).count(), 1
        )


class PostulacionArchivadaFilterTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@test.com", "x")
        self.user = User.objects.create(username="ana")
        self.conv = crear_convocatoria()
        self.activa = Postulacion.objects.create(user=self.user, convocatoria=self.conv, estado="enviado")
        self.archivada = Postulacion.objects.create(
            user=self.user, convocatoria=self.conv, estado="no_seleccionado",
            documentacion_depurada=timezone.now(),
        )
        self.url = reverse("admin:convocatorias_postulacion_changelist")

    def test_oculta_archivadas_por_defecto(self):
        self.client.force_login(self.superuser)
        ids = [p.pk for p in self.client.get(self.url).context["cl"].result_list]
        self.assertIn(self.activa.pk, ids)
        self.assertNotIn(self.archivada.pk, ids)

    def test_filtro_archivadas_las_muestra(self):
        self.client.force_login(self.superuser)
        ids = [p.pk for p in self.client.get(self.url + "?archivada=archivadas").context["cl"].result_list]
        self.assertIn(self.archivada.pk, ids)
        self.assertNotIn(self.activa.pk, ids)


class FiltrosPersistentesTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@test.com", "x")
        self.client.force_login(self.superuser)
        self.url = reverse("admin:convocatorias_postulacion_changelist")

    def test_recuerda_filtros_al_reingresar(self):
        # El admin filtra por estado
        r = self.client.get(self.url + "?estado=enviado")
        self.assertEqual(r.status_code, 200)
        # Reingresa "fresco" (sin referer): lo devuelve a sus filtros
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("estado=enviado", r["Location"])

    def test_boton_limpiar_no_restaura(self):
        self.client.get(self.url + "?estado=enviado")
        # Clic en "✕": viene de la propia lista → no debe redirigir a los filtros
        r = self.client.get(self.url, HTTP_REFERER="http://testserver" + self.url)
        self.assertEqual(r.status_code, 200)
        # Y a partir de ahí queda sin filtros guardados
        r2 = self.client.get(self.url)
        self.assertEqual(r2.status_code, 200)


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class PlanillaRendicionCleanupTest(TestCase):
    """La planilla .xlsx de la rendición no debe quedar huérfana al borrar,
    limpiar o reemplazar."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create(username="ana")
        self.conv = crear_convocatoria()
        self.post = Postulacion.objects.create(
            user=self.user, convocatoria=self.conv, estado="finalizado"
        )

    def _rendicion_con_planilla(self, nombre="planilla.xlsx"):
        r = Rendicion.objects.create(
            postulacion=self.post, user=self.user, estado="ENVIADO",
            planilla_xlsx=SimpleUploadedFile(nombre, b"PK planilla"),
        )
        return r, r.planilla_xlsx.path

    def test_borrar_rendicion_borra_planilla(self):
        r, archivo = self._rendicion_con_planilla()
        self.assertTrue(os.path.exists(archivo))
        r.delete()
        self.assertFalse(os.path.exists(archivo))

    def test_borrar_postulacion_borra_planilla_en_cascada(self):
        r, archivo = self._rendicion_con_planilla()
        self.assertTrue(os.path.exists(archivo))
        self.post.delete()
        self.assertFalse(Rendicion.objects.filter(pk=r.pk).exists())
        self.assertFalse(os.path.exists(archivo), "la planilla no debe quedar huérfana")

    def test_reemplazar_planilla_borra_la_anterior(self):
        r, archivo_viejo = self._rendicion_con_planilla("vieja.xlsx")
        r.planilla_xlsx = SimpleUploadedFile("nueva.xlsx", b"PK nueva")
        r.save()
        archivo_nuevo = r.planilla_xlsx.path
        self.assertFalse(os.path.exists(archivo_viejo), "la planilla vieja debe borrarse")
        self.assertTrue(os.path.exists(archivo_nuevo))

    def test_limpiar_planilla_borra_el_archivo(self):
        r, archivo = self._rendicion_con_planilla()
        r.planilla_xlsx = None
        r.save()
        self.assertFalse(os.path.exists(archivo))
