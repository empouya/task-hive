from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []


# Database
DATABASES = {
    'default': env.db("DATABASE_URL")
}