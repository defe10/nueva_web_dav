from .base import *

# ======================================================
# PRODUCCIÓN / PREPRODUCCIÓN
# ======================================================

DEBUG = False

ALLOWED_HOSTS = [
    "defe10.pythonanywhere.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://defe10.pythonanywhere.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


# ======================================================
# EMAIL (SMTP REAL)
# ======================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# 🔒 Credenciales fuera de Git
from .secrets import (
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
    DEFAULT_FROM_EMAIL,
)
