from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from sitio_publico import views as sitio_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Página de inicio
    path('', sitio_views.inicio, name='inicio'),

    # Usuarios (login, registro, panel, etc.)
    path('usuarios/', include('usuarios.urls')),

    # Registro Audiovisual
    path('registro/', include('registro_audiovisual.urls')),

    # Convocatorias
    path('convocatorias/', include('convocatorias.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
