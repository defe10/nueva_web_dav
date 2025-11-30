from django.shortcuts import render

def inicio(request):
    return render(request, 'sitio_publico/inicio.html')
