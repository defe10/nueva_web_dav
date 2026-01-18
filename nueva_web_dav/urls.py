from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Sitio público (home, institucional, etc.)
    path("", include("sitio_publico.urls")),

    # Usuarios
    path("usuarios/", include("usuarios.urls")),

    # Registro base
    path("registro/", include("registro_audiovisual.urls")),

    # Convocatorias
    path("convocatorias/", include("convocatorias.urls")),

    # Exención
    path("exencion/", include("exencion.urls")),

    # Backoffice
    path("backoffice/", include("backoffice.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
