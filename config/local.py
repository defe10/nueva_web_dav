from .base import *

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "federicocasoni@edusalta.gov.ar"
EMAIL_HOST_PASSWORD = "hjsl sydv wmhw oqcb"  # contraseña de aplicación
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

