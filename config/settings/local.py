from .base import *
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.abspath(__file__), '.env')
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ["*"]

DEBUG = os.environ.get('DEBUG')
PRODUCTION = os.environ.get('PRODUCTION')


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'media')
]

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
