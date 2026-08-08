import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "writing_agent",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "django.middleware.common.CommonMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.debug',
                "django.template.context_processors.request",
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
