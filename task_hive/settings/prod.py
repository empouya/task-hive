from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# SECURITY SETTINGS
# These ensure the app only communicates over HTTPS in production
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# DATABASE
DATABASES = {
    'default': env.db("DATABASE_URL")
}

# SPECTACULAR SETTINGS (Optional: hide docs in prod or keep them)
SPECTACULAR_SETTINGS = {
    'SERVE_INCLUDE_SCHEMA': False,
}