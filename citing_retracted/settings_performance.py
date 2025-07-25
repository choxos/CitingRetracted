from .settings_production import *
import os

# ============================================================================
# PERFORMANCE OPTIMIZATIONS FOR PRCT
# ============================================================================

# Database Performance
DATABASES['default'].update({
    'CONN_MAX_AGE': 600,  # Persistent connections
    'OPTIONS': {
        'MAX_CONNS': 20,
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
})

# Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'prct',
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 86400,  # 24 hours
        'KEY_PREFIX': 'prct_sessions',
    },
    'analytics': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',
        'TIMEOUT': 3600,  # 1 hour for analytics data
        'KEY_PREFIX': 'prct_analytics',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False

# Template Caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Static Files Optimization
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise middleware for static file serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static file compression and caching
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False
WHITENOISE_MAX_AGE = 31536000  # 1 year cache

# Security optimizations
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database query optimization
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Pagination settings
PAGINATE_BY = 25
MAX_PAGE_SIZE = 100

# Analytics caching settings
ANALYTICS_CACHE_TIMEOUT = 3600  # 1 hour
ANALYTICS_CACHE_KEY_PREFIX = 'analytics'

# Performance monitoring
LOGGING['loggers'].update({
    'django.db.backends': {
        'level': 'DEBUG' if DEBUG else 'INFO',
        'handlers': ['console'],
        'propagate': False,
    },
    'django.request': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
        'propagate': False,
    }
})

# Email configuration (for error reporting)
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@prct.xeradb.com')
    
    ADMINS = [
        ('PRCT Admin', os.getenv('ADMIN_EMAIL', 'admin@prct.xeradb.com')),
    ]

# Data loading optimizations
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Analytics optimization settings
ANALYTICS_BATCH_SIZE = 1000
ANALYTICS_PREFETCH_SIZE = 500
CITATION_FETCH_BATCH_SIZE = 100 