from .base import *
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(" ")

DEBUG = os.environ.get('DEBUG')
PRODUCTION = os.environ.get('PRODUCTION')


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('NAME'),
        'USER': os.environ.get('USER'),
        'PASSWORD': os.environ.get('PASSWORD'),
        'HOST': os.environ.get('HOST'),
        'PORT': os.environ.get('PORT'),
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app/static'),
    os.path.join(BASE_DIR, 'app/media')
]

STATIC_URL = 'app/static/'
MEDIA_URL = 'app/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'app/staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'app/mediafiles')
