from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from sitio_publico import views as sitio_views


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home pública
    path('', sitio_views.inicio, name='inicio'),

    # Usuarios (login, registro, panel, recuperación de contraseña)
    path('usuarios/', include('usuarios.urls')),

    # Registro base (persona humana / jurídica)
    path('registro/', include('registro_audiovisual.urls')),

    # Convocatorias (concursos, programas, cursos, incentivos)
    path('convocatorias/', include('convocatorias.urls')),

    # Beneficios – Exención
    path('exencion/', include('exencion.urls')),

    path("", include("sitio_publico.urls")),
]


# Archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
