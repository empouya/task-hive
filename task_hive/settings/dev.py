from .base import *

DEBUG = True

DATABASES = {
    "default": env.db("DATABASE_URL")
}