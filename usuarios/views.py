from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegistroUsuarioForm, LoginForm

def registro(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect("panel_usuario")
    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})


def login_usuario(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("panel_usuario")
    else:
        form = LoginForm()
    return render(request, "usuarios/login.html", {"form": form})


def logout_usuario(request):
    logout(request)
    return redirect("inicio")


def panel_usuario(request):
    return render(request, "usuarios/panel.html")

def registrar_usuario(request):
    return render(request, 'usuarios/registrar.html')

