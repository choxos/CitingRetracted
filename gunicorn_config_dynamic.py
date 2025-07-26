import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
PRCT_PORT = os.getenv('PRCT_PORT', '8001')
PRCT_HOST = os.getenv('PRCT_HOST', '127.0.0.1')
PRCT_WORKERS = int(os.getenv('PRCT_WORKERS', '3'))

# Gunicorn configuration
bind = f"{PRCT_HOST}:{PRCT_PORT}"
workers = PRCT_WORKERS
worker_class = "sync"
worker_connections = 1000
max_requests = 2000
max_requests_jitter = 200
timeout = 60
keepalive = 5
user = "xeradb"
group = "xeradb"
preload_app = True
tmp_upload_dir = None
errorlog = "/var/log/prct/gunicorn_error.log"
accesslog = "/var/log/prct/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"

# Print configuration for debugging
print(f"🚀 Gunicorn starting on {bind} with {workers} workers")
print(f"📊 Configuration loaded from .env file") 