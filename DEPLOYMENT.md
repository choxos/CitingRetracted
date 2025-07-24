# Deployment Guide

This guide covers deploying the Post-Retraction Citation Tracker (PRCT) application locally and on various cloud platforms.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ (for production)
- Redis (for caching and task queue)
- Docker and Docker Compose (for containerized deployment)

## Local Development

### Option 1: Docker Compose (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd CitingRetracted
   ```

2. **Build and start services:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database on port 5432
   - Redis server on port 6379
   - Django web application on port 8000
   - Celery worker for background tasks
   - Celery Beat scheduler for automated daily updates

3. **Initialize database:**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Import initial data:**
   ```bash
   # Import retracted papers (requires Retraction Watch CSV)
   docker-compose exec web python manage.py import_retraction_watch data/retractionwatch_data.csv

   # Fetch citations for papers
   docker-compose exec web python manage.py fetch_citations --limit 10
   ```

### Option 2: Local Installation

### Prerequisites
- Python 3.8+ installed
- Git installed
- PostgreSQL (optional, SQLite works for development)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd CitingRetracted
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the project root:
   ```env
   DEBUG=True
   SECRET_KEY=your-local-secret-key-here
   DATABASE_URL=sqlite:///db.sqlite3
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Import Sample Data**
   ```bash
   # Import first 50 retracted papers
   python manage.py import_retraction_watch --limit 50
   
   # Fetch citations for first 10 papers
   python manage.py fetch_citations --limit 10
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```
   
   Access the application at: http://localhost:8000

---

## Scheduled Tasks

The application includes automated daily refresh tasks:

### **Daily Refresh Schedule (8:00 AM EST):**
- **8:00 AM EST (1:00 PM UTC):** Refresh retracted papers from Retraction Watch
- **8:30 AM EST (1:30 PM UTC):** Fetch new citations from APIs

### **Manual Task Management:**

1. **Check task status:**
   ```bash
   # In Docker
   docker-compose exec web python manage.py shell
   
   # In shell
   from papers.tasks import refresh_retracted_papers, refresh_citations
   
   # Run tasks manually
   refresh_retracted_papers.delay()
   refresh_citations.delay()
   ```

2. **Monitor Celery workers:**
   ```bash
   # View worker status
   docker-compose logs celery
   
   # View scheduler status
   docker-compose logs celery-beat
   ```

3. **Manage scheduled tasks in Django Admin:**
   - Go to `/admin/django_celery_beat/`
   - View and modify periodic tasks
   - Monitor task execution history

### **Production Celery Setup:**

For production deployments, ensure:
- Redis is properly configured and secured
- Celery workers have sufficient resources
- Task monitoring and alerting is in place
- Log retention policies are configured

## ☁️ Google Cloud Platform Deployment

### Prerequisites
- Google Cloud account with billing enabled
- Google Cloud SDK installed locally
- Docker installed (optional)

### Method 1: App Engine (Recommended for beginners)

#### 1. **Prepare Your Project**

Create `app.yaml`:
```yaml
runtime: python39

env_variables:
  DEBUG: "False"
  SECRET_KEY: "your-production-secret-key"
  DATABASE_URL: "postgresql://username:password@/db_name?host=/cloudsql/project:region:instance"
  ALLOWED_HOSTS: "your-app-id.appspot.com"

handlers:
- url: /static
  static_dir: staticfiles/
- url: /.*
  script: auto

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

Create `requirements-gcp.txt`:
```txt
Django>=4.2,<5.0
requests>=2.31.0
pandas>=2.1.0
numpy>=1.24.0
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
django-bootstrap5>=23.3
whitenoise>=6.6.0
gunicorn>=21.2.0
celery>=5.3.0
redis>=5.0.0
django-extensions>=3.2.0
plotly>=5.17.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
psycopg2-binary>=2.9.0
google-cloud-storage>=2.0.0
```

#### 2. **Set up Cloud SQL (PostgreSQL)**

```bash
# Create Cloud SQL instance
gcloud sql instances create citing-retracted-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create citing_retracted_db \
    --instance=citing-retracted-db

# Create user
gcloud sql users create app_user \
    --instance=citing-retracted-db \
    --password=secure_password_here
```

#### 3. **Update Django Settings**

Create `settings_production.py`:
```python
from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = ['.appspot.com', 'localhost']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'citing_retracted_db',
        'USER': 'app_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': f'/cloudsql/{os.environ.get("CLOUD_SQL_CONNECTION_NAME")}',
        'PORT': '',
    }
}

# Static files
STATIC_ROOT = 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

#### 4. **Deploy to App Engine**

```bash
# Initialize gcloud
gcloud init
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud app deploy

# Run migrations
gcloud app exec -- python manage.py migrate

# Create superuser (optional)
gcloud app exec -- python manage.py createsuperuser
```

### Method 2: Cloud Run (Docker)

#### 1. **Create Dockerfile**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn citing_retracted.wsgi:application --bind 0.0.0.0:$PORT"]
```

#### 2. **Build and Deploy**

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/citing-retracted

# Deploy to Cloud Run
gcloud run deploy citing-retracted \
    --image gcr.io/YOUR_PROJECT_ID/citing-retracted \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DEBUG=False,SECRET_KEY=your-secret \
    --set-cloudsql-instances YOUR_PROJECT_ID:us-central1:citing-retracted-db
```

---

## 🚂 Railway Deployment

Railway provides an easy deployment option with built-in PostgreSQL.

### Method 1: GitHub Integration (Recommended)

#### 1. **Prepare Your Repository**

Create `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Create `Procfile`:
```
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn citing_retracted.wsgi:application --bind 0.0.0.0:$PORT
```

#### 2. **Update Settings for Railway**

Create `settings_railway.py`:
```python
from .settings import *
import os

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']  # Railway handles the proxy

# Database - Railway provides DATABASE_URL
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

Update `wsgi.py`:
```python
import os
from django.core.wsgi import get_wsgi_application

# Use Railway settings if on Railway
if 'RAILWAY_ENVIRONMENT' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings_railway')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')

application = get_wsgi_application()
```

Add to `requirements.txt`:
```txt
dj-database-url>=2.0.0
```

#### 3. **Deploy via Railway Dashboard**

1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add PostgreSQL service:
   - Click "New" → "Database" → "PostgreSQL"
6. Set environment variables in Railway dashboard:
   ```
   DEBUG=False
   SECRET_KEY=your-very-secure-secret-key-here
   DJANGO_SETTINGS_MODULE=citing_retracted.settings_railway
   ```
7. Deploy automatically triggers

#### 4. **Post-Deployment Setup**

```bash
# Connect to Railway CLI
npm install -g @railway/cli
railway login

# Run one-time commands
railway run python manage.py createsuperuser
railway run python manage.py import_retraction_watch --limit 100
```

### Method 2: Railway CLI

#### 1. **Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

#### 2. **Initialize and Deploy**
```bash
# In your project directory
railway init
railway add postgresql
railway up
```

#### 3. **Set Environment Variables**
```bash
railway variables set DEBUG=False
railway variables set SECRET_KEY=your-secret-key
railway variables set DJANGO_SETTINGS_MODULE=citing_retracted.settings_railway
```

---

## 🔧 Production Optimizations

### Redis for Caching (Recommended for all platforms)

**Google Cloud:**
```bash
gcloud redis instances create citing-retracted-cache \
    --size=1 \
    --region=us-central1
```

**Railway:**
Add Redis service in Railway dashboard.

**Django Settings:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Celery for Background Tasks

Create `celery.py`:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')

app = Celery('citing_retracted')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Environment-Specific Requirements

Create separate requirements files:

**requirements-dev.txt:**
```txt
-r requirements.txt
django-debug-toolbar==4.2.0
pytest-django==4.5.2
coverage==7.3.0
```

**requirements-prod.txt:**
```txt
-r requirements.txt
psycopg2-binary==2.9.7
gunicorn==21.2.0
whitenoise==6.6.0
django-redis==5.4.0
```

---

## 🔒 Security Checklist

### Before Production Deployment:

- [ ] Change `SECRET_KEY` to a secure, random value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use HTTPS (SSL certificates)
- [ ] Set up proper database user permissions
- [ ] Enable Django security middleware
- [ ] Configure CORS if needed
- [ ] Set up monitoring and logging
- [ ] Regular backups of database
- [ ] Update dependencies regularly

### Environment Variables Template:

```env
# Core Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-minimum-50-characters-long
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# External APIs (Optional - for citation fetching)
OPENALEX_EMAIL=your-email@domain.com

# Caching (Optional)
REDIS_URL=redis://localhost:6379/1

# File Storage (Optional - for production)
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

---

## 🎯 Quick Start Commands

### Local Development:
```bash
git clone <repo>
cd CitingRetracted
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Railway Deployment:
```bash
railway init
railway add postgresql
railway up
railway run python manage.py migrate
```

### Google Cloud Deployment:
```
```