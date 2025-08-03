from .settings import *
import os
from dotenv import load_dotenv

# Load environment variables from .env file (override system env)
load_dotenv(override=True)

# Production settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'prct.xeradb.com',
    'www.prct.xeradb.com', 
    '91.99.161.136',
    'localhost',
    '127.0.0.1',
    'xeradb.com'
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prct_production',
        'USER': 'prct_user',
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': '127.0.0.1',  # Use IPv4 explicitly to avoid IPv6 issues
        'PORT': '5432',
    }
}

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY')

# Port Configuration
PRCT_PORT = int(os.getenv('PRCT_PORT', '8001'))
PRCT_HOST = os.getenv('PRCT_HOST', '127.0.0.1')

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/prct/static/'
STATICFILES_DIRS = []  # Empty for production to avoid conflicts

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files  
MEDIA_ROOT = '/var/www/prct/media/'
MEDIA_URL = '/media/'

# Security settings for production
SECURE_SSL_REDIRECT = True  # Set to False if not using HTTPS yet
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF protection
CSRF_TRUSTED_ORIGINS = [
    'https://prct.xeradb.com',
    'https://www.prct.xeradb.com',
    'http://91.99.161.136:8000',
    'http://91.99.161.136:8001'
]

# Performance
USE_TZ = True
TIME_ZONE = 'UTC'

# Simplified logging (logs to both console and file)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/prct/django.log',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Google Analytics Configuration
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '') 