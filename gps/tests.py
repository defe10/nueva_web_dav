from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from convocatorias.models import Convocatoria, Postulacion
from gps.models import Obra
from registro_audiovisual.models import PersonaHumana


def crear_usuario(username="titular", con_registro=True, **kwargs):
    user = User.objects.create_user(username=username, password="x", **kwargs)
    if con_registro:
        PersonaHumana.objects.create(
            user=user,
            nombre="Juana",
            apellido="Pérez",
            cuil_cuit="27123456789",
            fecha_nacimiento=date(1990, 1, 1),
            genero="femenino",
            nivel_educativo="universitario",
            lugar_residencia="capital",
            domicilio_real="Calle 1",
            codigo_postal_real="4400",
            telefono="3870000000",
            email=f"{username}@test.com",
        )
    return user


@override_settings(GPS_ACTIVO=True)
class AccesoGpsTest(TestCase):
    """El GPS exige Registro Audiovisual, igual que exención."""

    def test_sin_registro_redirige_al_registro(self):
        self.client.force_login(crear_usuario(con_registro=False))
        resp = self.client.get(reverse("gps:mis_obras"))
        destino = reverse("registro_audiovisual:seleccionar_tipo_registro")
        self.assertRedirects(
            resp, f"{destino}?next={reverse('gps:mis_obras')}",
            fetch_redirect_response=False,
        )

    def test_crear_obra_sin_registro_redirige_al_registro(self):
        self.client.force_login(crear_usuario(con_registro=False))
        resp = self.client.get(reverse("gps:obra_crear"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("registro", resp["Location"])

    def test_con_registro_entra(self):
        self.client.force_login(crear_usuario())
        self.assertEqual(self.client.get(reverse("gps:mis_obras")).status_code, 200)

    def test_staff_no_necesita_registro(self):
        self.client.force_login(crear_usuario("admin", con_registro=False, is_staff=True))
        self.assertEqual(self.client.get(reverse("gps:mis_obras")).status_code, 200)

    def test_mis_obras_solo_muestra_las_propias(self):
        propia = Obra.objects.create(owner=crear_usuario("uno"), titulo="Obra propia")
        Obra.objects.create(owner=crear_usuario("dos"), titulo="Obra ajena")
        self.client.force_login(propia.owner)
        html = self.client.get(reverse("gps:mis_obras")).content.decode()
        self.assertIn("Obra propia", html)
        self.assertNotIn("Obra ajena", html)

    def test_staff_no_ve_las_obras_de_otros(self):
        """El listado completo vive en /admin, no en 'Mis obras'."""
        Obra.objects.create(owner=crear_usuario("uno"), titulo="Obra ajena")
        self.client.force_login(crear_usuario("admin", con_registro=False, is_staff=True))
        html = self.client.get(reverse("gps:mis_obras")).content.decode()
        self.assertNotIn("Obra ajena", html)


@override_settings(GPS_ACTIVO=True)
class PanelObrasTest(TestCase):
    """Sección 'Registro de obras' dentro del panel del usuario."""

    def test_panel_lista_las_obras_del_usuario(self):
        user = crear_usuario()
        Obra.objects.create(owner=user, titulo="Mi cortometraje")
        self.client.force_login(user)
        html = self.client.get(reverse("usuarios:panel_usuario")).content.decode()
        self.assertIn("Registro de obras", html)
        self.assertIn("Mi cortometraje", html)

    def test_panel_muestra_la_seccion_aunque_no_haya_obras(self):
        self.client.force_login(crear_usuario())
        html = self.client.get(reverse("usuarios:panel_usuario")).content.decode()
        self.assertIn("Registro de obras", html)
        self.assertIn("Registrar obra", html)

    def test_panel_sin_registro_no_muestra_la_seccion(self):
        self.client.force_login(crear_usuario(con_registro=False))
        html = self.client.get(reverse("usuarios:panel_usuario")).content.decode()
        self.assertNotIn("Registro de obras", html)


def datos_obra(**extra):
    """POST mínimo válido para ObraForm."""
    datos = {
        "titulo": "Los ríos",
        "anio_inicio": 2024,
        "estado_produccion": "desarrollo",
    }
    datos.update(extra)
    return datos


@override_settings(GPS_ACTIVO=True)
class TitulosAnterioresTest(TestCase):
    """Una obra puede cambiar de nombre y hay que poder reconocerla igual."""

    def setUp(self):
        self.user = crear_usuario()
        self.client.force_login(self.user)

    def test_renombrar_archiva_el_titulo_viejo(self):
        obra = Obra.objects.create(owner=self.user, titulo="El río")
        obra.titulo = "Los ríos"
        obra.save()
        anterior = obra.titulos_anteriores.get()
        self.assertEqual(anterior.titulo, "El río")
        self.assertTrue(anterior.automatico)
        self.assertEqual(anterior.anio_hasta, date.today().year)

    def test_dos_renombres_archivan_los_dos_titulos(self):
        obra = Obra.objects.create(owner=self.user, titulo="A")
        for nuevo in ("B", "C"):
            obra.titulo = nuevo
            obra.save()
        self.assertEqual(
            set(obra.titulos_anteriores.values_list("titulo", flat=True)), {"A", "B"},
        )

    def test_volver_a_un_titulo_previo_lo_saca_de_los_anteriores(self):
        obra = Obra.objects.create(owner=self.user, titulo="A")
        obra.titulo = "B"
        obra.save()
        obra.titulo = "A"
        obra.save()
        self.assertEqual(
            list(obra.titulos_anteriores.values_list("titulo", flat=True)), ["B"],
        )

    def test_guardar_sin_cambiar_el_titulo_no_archiva_nada(self):
        obra = Obra.objects.create(owner=self.user, titulo="El río")
        obra.sinopsis = "Otra cosa"
        obra.save()
        self.assertFalse(obra.titulos_anteriores.exists())

    def test_se_puede_cargar_un_titulo_anterior_al_crear_la_obra(self):
        self.client.post(
            reverse("gps:obra_crear"),
            datos_obra(titulo_anterior_nuevo="El río (desarrollo)"),
        )
        obra = Obra.objects.get(owner=self.user)
        self.assertEqual(
            list(obra.titulos_anteriores.values_list("titulo", flat=True)),
            ["El río (desarrollo)"],
        )

    def test_el_titular_puede_agregar_un_titulo_a_mano(self):
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        self.client.post(
            reverse("gps:obra_editar", args=[obra.pk]),
            datos_obra(titulo_anterior_nuevo="El río (desarrollo)"),
        )
        self.assertEqual(
            list(obra.titulos_anteriores.values_list("titulo", flat=True)),
            ["El río (desarrollo)"],
        )

    def test_no_se_guarda_un_titulo_anterior_igual_al_actual(self):
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        self.client.post(
            reverse("gps:obra_editar", args=[obra.pk]),
            datos_obra(titulo_anterior_nuevo="Los ríos"),
        )
        self.assertFalse(obra.titulos_anteriores.exists())

    def test_el_titular_puede_quitar_un_titulo(self):
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        anterior = obra.titulos_anteriores.create(titulo="Error de tipeo")
        self.client.post(
            reverse("gps:obra_editar", args=[obra.pk]),
            datos_obra(titulos_anteriores_eliminar=[anterior.pk]),
        )
        self.assertFalse(obra.titulos_anteriores.exists())

    def test_el_detalle_muestra_los_titulos_anteriores(self):
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        obra.titulos_anteriores.create(titulo="El río", anio_hasta=2023)
        html = self.client.get(
            reverse("gps:obra_detalle", args=[obra.pk])
        ).content.decode()
        self.assertIn("Antes:", html)
        self.assertIn("El río", html)
        self.assertIn("hasta 2023", html)


def crear_postulacion(user, estado="seleccionado", titulo="Plan de Fomento 2024",
                      nombre_proyecto="El río", **extra):
    convocatoria, _ = Convocatoria.objects.get_or_create(
        slug=titulo.lower().replace(" ", "-"),
        defaults={
            "titulo": titulo,
            "categoria": "CONCURSO",
            "linea": "fomento",
            "fecha_inicio": date(2024, 1, 1),
            "fecha_fin": date(2024, 12, 31),
        },
    )
    return Postulacion.objects.create(
        user=user, convocatoria=convocatoria, nombre_proyecto=nombre_proyecto,
        estado=estado, **extra,
    )


@override_settings(GPS_ACTIVO=True)
class VincularPostulacionesTest(TestCase):
    """El titular vincula la obra con sus postulaciones; nunca con las de otro."""

    def setUp(self):
        self.user = crear_usuario()
        self.client.force_login(self.user)

    def test_el_formulario_ofrece_solo_las_postulaciones_propias(self):
        mia = crear_postulacion(self.user)
        ajena = crear_postulacion(crear_usuario("otro"), titulo="Otra convocatoria")
        elegibles = self.client.get(
            reverse("gps:obra_crear")
        ).context["form"].fields["postulaciones"].queryset
        self.assertIn(mia, elegibles)
        self.assertNotIn(ajena, elegibles)

    def test_no_ofrece_borradores(self):
        borrador = crear_postulacion(self.user, estado="borrador")
        elegibles = self.client.get(
            reverse("gps:obra_crear")
        ).context["form"].fields["postulaciones"].queryset
        self.assertNotIn(borrador, elegibles)

    def test_al_crear_la_obra_queda_vinculada(self):
        postulacion = crear_postulacion(self.user)
        self.client.post(
            reverse("gps:obra_crear"),
            datos_obra(postulaciones=[postulacion.pk]),
        )
        obra = Obra.objects.get(owner=self.user)
        self.assertEqual(list(obra.postulaciones.all()), [postulacion])

    def test_no_se_puede_vincular_la_postulacion_de_otro(self):
        ajena = crear_postulacion(crear_usuario("otro"))
        resp = self.client.post(
            reverse("gps:obra_crear"),
            datos_obra(postulaciones=[ajena.pk]),
        )
        self.assertFalse(Obra.objects.exists())
        self.assertIn("postulaciones", resp.context["form"].errors)


@override_settings(GPS_ACTIVO=True)
class ClaimGanadoresTest(TestCase):
    """Los proyectos seleccionados se avisan en el panel y prellenan la obra."""

    def setUp(self):
        self.user = crear_usuario()
        self.client.force_login(self.user)

    def _panel(self):
        return self.client.get(reverse("usuarios:panel_usuario"))

    def test_el_panel_avisa_de_los_seleccionados_sin_obra(self):
        postulacion = crear_postulacion(self.user)
        resp = self._panel()
        self.assertIn(postulacion, resp.context["postulaciones_sin_obra"])
        self.assertIn("sin obra registrada", resp.content.decode())

    def test_el_panel_no_avisa_de_los_que_no_ganaron(self):
        crear_postulacion(self.user, estado="no_seleccionado")
        self.assertFalse(self._panel().context["postulaciones_sin_obra"])

    def test_el_aviso_desaparece_al_registrar_la_obra(self):
        postulacion = crear_postulacion(self.user)
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        obra.postulaciones.add(postulacion)
        self.assertFalse(self._panel().context["postulaciones_sin_obra"])

    def test_el_formulario_se_prellena_con_la_postulacion(self):
        postulacion = crear_postulacion(
            self.user, tipo_proyecto="cine_largo", genero="documental",
            sinopsis_corta="Un río que se seca.",
        )
        inicial = self.client.get(
            f"{reverse('gps:obra_crear')}?postulacion={postulacion.pk}"
        ).context["form"].initial
        self.assertEqual(inicial["titulo"], "El río")
        self.assertEqual(inicial["formato"], "largometraje")
        self.assertEqual(inicial["genero"], "documental")
        self.assertEqual(inicial["sinopsis"], "Un río que se seca.")
        self.assertEqual(inicial["postulaciones"], [postulacion.pk])

    def test_no_se_prellena_con_la_postulacion_de_otro(self):
        ajena = crear_postulacion(crear_usuario("otro"))
        inicial = self.client.get(
            f"{reverse('gps:obra_crear')}?postulacion={ajena.pk}"
        ).context["form"].initial
        self.assertNotIn("titulo", inicial)


@override_settings(GPS_ACTIVO=False)
class GpsDesactivadoTest(TestCase):
    """Con el módulo apagado el GPS queda invisible y sin URLs.

    Es lo que permite subirlo al servidor sin abrirlo al público.
    """

    def setUp(self):
        self.user = crear_usuario()
        self.client.force_login(self.user)

    def test_las_vistas_dan_404(self):
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        for url in (
            reverse("gps:mis_obras"),
            reverse("gps:obra_crear"),
            reverse("gps:obra_detalle", args=[obra.pk]),
            reverse("gps:hito_crear", args=[obra.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_el_panel_no_muestra_la_seccion(self):
        Obra.objects.create(owner=self.user, titulo="Mi cortometraje")
        html = self.client.get(reverse("usuarios:panel_usuario")).content.decode()
        self.assertNotIn("Registro de obras", html)
        self.assertNotIn("Mi cortometraje", html)

    def test_el_banner_de_tramites_no_muestra_el_acceso(self):
        html = self.client.get(reverse("sitio_publico:inicio")).content.decode()
        self.assertNotIn("Registro de obras", html)
        # El resto del banner sigue en su lugar.
        self.assertIn("Exención impositiva", html)

    def test_el_admin_sigue_funcionando(self):
        """El staff tiene que poder cargar obras mientras el módulo está cerrado."""
        obra = Obra.objects.create(owner=self.user, titulo="Los ríos")
        admin = User.objects.create_superuser("jefa", "jefa@test.com", "x")
        self.client.force_login(admin)
        resp = self.client.get(f"/admin/gps/obra/{obra.pk}/change/")
        self.assertEqual(resp.status_code, 200)
