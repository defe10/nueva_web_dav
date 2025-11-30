"""
URL configuration for nueva_web_dav project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from sitio_publico import views as sitio_views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Página de inicio
    path('', sitio_views.inicio, name='inicio'),
    path('usuarios/', include('usuarios.urls')),
    path('registro/', include('registro_audiovisual.urls')),
    path('convocatorias/', include('convocatorias.urls')),




 
  
  

]

# Archivos subidos por usuarios (DNI, PDFs, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

