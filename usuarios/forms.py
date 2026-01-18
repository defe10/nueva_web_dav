from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm


# =====================================================
# LOGIN
# =====================================================
class LoginForm(AuthenticationForm):

    # Campo honeypot (invisible al usuario)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput())

    username = forms.CharField(
        label="Correo electrónico",
        widget=forms.TextInput(attrs={"placeholder": "tu@email.com"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Ingresá tu contraseña"})
    )

    def clean_honeypot(self):
        """
        Si este campo invisible tiene contenido → bot detectado.
        """
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Error inesperado.")
        return ""


# =====================================================
# REGISTRO DE USUARIO
# =====================================================
class RegistroUsuarioForm(forms.ModelForm):

    # Campo honeypot (invisible al usuario)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput())

    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre"})
    )

    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Tu apellido"})
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Ingresá tu contraseña"})
    )

    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repetí tu contraseña"})
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "tu@email.com"}),
        }

    # ------------------------
    # VALIDACIONES
    # ------------------------
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_honeypot(self):
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Error inesperado.")
        return ""

    # ------------------------
    # GUARDADO
    # ------------------------
    def save(self, commit=True):
        user = super().save(commit=False)

        email = self.cleaned_data["email"]

        user.username = email
        user.email = email
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # activación por email

        if commit:
            user.save()

        return user


# =====================================================
# RECUPERACIÓN DE CONTRASEÑA
# =====================================================
class PasswordResetEmailForm(PasswordResetForm):

    # Campo honeypot invisible
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_honeypot(self):
        """
        Si este campo viene con contenido → bot detectado.
        """
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Error inesperado.")
        return ""
