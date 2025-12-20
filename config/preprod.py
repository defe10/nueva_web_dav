from .base import *

DEBUG = False

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://defe10.pythonanywhere.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


# ============================================
# EMAIL
# ============================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "federicocasoni@edusalta.gov.ar"
EMAIL_HOST_PASSWORD = "qmyw qjxc iyve bpbr"

DEFAULT_FROM_EMAIL = "Dirección de Audiovisuales <federicocasoni@edusalta.gov.ar>"

