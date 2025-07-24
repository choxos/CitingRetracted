# 🚀 Deploy PRCT to Hetzner VPS - Post-Retraction Citation Tracker

Deploy Post-Retraction Citation Tracker to your Hetzner VPS at `91.99.161.136` following the Xera DB ecosystem structure.

## 📋 Pre-Deployment Checklist

1. ✅ VPS is running (91.99.161.136)
2. ✅ SSH access as root or xeradb user
3. ✅ Domain `prct.xeradb.com` pointed to 91.99.161.136
4. ✅ Existing Xera DB ecosystem setup completed
5. ✅ PostgreSQL and Nginx already configured

## 🔧 Step 1: Database Setup

```bash
# Connect to your VPS
ssh xeradb@91.99.161.136

# Switch to postgres user and create PRCT database
sudo -u postgres psql

-- In PostgreSQL prompt, run these commands:
CREATE DATABASE prct_production;
CREATE USER prct_user WITH PASSWORD 'PRCTSecure2025';
GRANT ALL PRIVILEGES ON DATABASE prct_production TO prct_user;
ALTER USER prct_user CREATEDB;
ALTER USER prct_user WITH SUPERUSER;
\q

# Fix PostgreSQL permissions (CRITICAL - prevents migration errors)
sudo -u postgres psql -d prct_production << 'EOF'
GRANT ALL ON SCHEMA public TO prct_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prct_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prct_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO prct_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO prct_user;
\q
EOF

# Test database connection
psql -h localhost -U prct_user -d prct_production -c "SELECT current_user, current_database();"
```

## 📁 Step 2: Deploy PRCT Application

```bash
# Create PRCT directory in ecosystem structure
sudo mkdir -p /var/www/prct
sudo chown -R xeradb:xeradb /var/www/prct

# Navigate to PRCT directory
cd /var/www/prct

# Clone PRCT repository
git clone https://github.com/choxos/CitingRetracted.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary python-dotenv openpyxl
```

## ⚙️ Step 3: Environment Configuration

```bash
# Generate a secure secret key and create .env file
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
cat > .env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_PASSWORD=PRCTSecure2025
ALLOWED_HOSTS=prct.xeradb.com,91.99.161.136,localhost,xeradb.com,127.0.0.1
STATIC_ROOT=/var/www/prct/staticfiles/
MEDIA_ROOT=/var/www/prct/media/
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
XERADB_PROJECT=prct
RAILWAY_ENVIRONMENT=production
EOF

# Verify .env file was created
cat .env
```

## 🐍 Step 4: Production Settings

```bash
# Create production settings
nano citing_retracted/production_settings.py
```

**Add to `citing_retracted/production_settings.py`:**
```python
from .settings import *
import os
from dotenv import load_dotenv

load_dotenv()

# Production settings
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prct_production',
        'USER': 'prct_user',
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = '/var/www/prct/staticfiles/'
STATIC_URL = '/static/'
MEDIA_ROOT = '/var/www/prct/media/'
MEDIA_URL = '/media/'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/www/prct/logs/django.log',
        },
    },
    'root': {
        'handlers': ['file'],
    },
}

# PRCT specific settings
PAPERS_PER_PAGE = 20

# Celery settings (if using background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
```

## 🚀 Step 5: Initialize Application

```bash
# Create logs directory
mkdir -p logs

# Set Django settings module
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
export RAILWAY_ENVIRONMENT=production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test the application
python manage.py runserver 0.0.0.0:8001
# Visit http://91.99.161.136:8001 to test
# Press Ctrl+C to stop when confirmed working
```

## 📊 Step 6: Import Retracted Papers Data

```bash
# Import retracted papers data (if you have the CSV files)
echo "Starting retracted papers import..."

# Create the management command if it doesn't exist
mkdir -p papers/management/commands/

# Create basic import command
cat > papers/management/commands/import_retracted_papers.py << 'EOF'
from django.core.management.base import BaseCommand
from papers.models import RetractedPaper, Citation
import pandas as pd
import os
from django.utils import timezone
from django.db import transaction

class Command(BaseCommand):
    help = 'Import retracted papers from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='CSV file path', default='data/retracted_papers.csv')
        parser.add_argument('--batch-size', type=int, help='Batch size for imports', default=1000)

    def handle(self, *args, **options):
        if not os.environ.get('RAILWAY_ENVIRONMENT'):
            self.stdout.write(self.style.WARNING('⚠️  Not in production environment. Skipping import.'))
            return

        file_path = options['file']
        batch_size = options['batch_size']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'❌ File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'📄 Importing retracted papers from {file_path}...'))

        try:
            df = pd.read_csv(file_path)
            self.stdout.write(f"Processing {len(df):,} records")

            papers = []
            for idx, row in df.iterrows():
                if idx % 1000 == 0:
                    self.stdout.write(f"  Processing {idx:,}/{len(df):,} records...")

                paper = RetractedPaper(
                    record_id=str(row.get('record_id', '')),
                    title=str(row.get('title', 'Unknown Title'))[:500],
                    author=str(row.get('author', ''))[:1000],
                    journal=str(row.get('journal', ''))[:200],
                    publisher=str(row.get('publisher', ''))[:200],
                    original_paper_date=pd.to_datetime(row.get('original_paper_date'), errors='coerce'),
                    retraction_date=pd.to_datetime(row.get('retraction_date'), errors='coerce'),
                    reason=str(row.get('reason', ''))[:1000],
                    subject=str(row.get('subject', ''))[:500],
                    country=str(row.get('country', ''))[:200],
                    institution=str(row.get('institution', ''))[:500],
                    original_paper_doi=str(row.get('doi', ''))[:200],
                    is_open_access=str(row.get('is_open_access', 'False')).lower() == 'true',
                )
                papers.append(paper)

                if len(papers) >= batch_size:
                    with transaction.atomic():
                        RetractedPaper.objects.bulk_create(papers, ignore_conflicts=True)
                    self.stdout.write(f'  ✅ Imported batch of {len(papers)} papers...')
                    papers = []

            if papers:
                with transaction.atomic():
                    RetractedPaper.objects.bulk_create(papers, ignore_conflicts=True)
                self.stdout.write(f'  ✅ Imported final batch of {len(papers)} papers')

            total_papers = RetractedPaper.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✅ Import completed! Total papers: {total_papers:,}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Import failed: {str(e)}'))
EOF

# If you have retracted papers data, import it
# python manage.py import_retracted_papers --file=/path/to/your/retracted_papers.csv

# For now, create some sample data to test the application
python manage.py shell -c "
from papers.models import RetractedPaper
from django.utils import timezone
import datetime

if RetractedPaper.objects.count() == 0:
    print('Creating sample retracted papers...')
    sample_papers = [
        {
            'record_id': 'SAMPLE001',
            'title': 'Sample Retracted Paper on COVID-19 Treatment',
            'author': 'John Doe; Jane Smith',
            'journal': 'Journal of Medical Research',
            'publisher': 'Sample Publisher',
            'original_paper_date': timezone.now().date() - datetime.timedelta(days=800),
            'retraction_date': timezone.now().date() - datetime.timedelta(days=100),
            'reason': 'Data fabrication; Unreliable results',
            'subject': 'Medicine - General; Biology - Molecular',
            'country': 'United States',
            'institution': 'Sample University Medical Center',
            'original_paper_doi': '10.1000/sample.001',
            'is_open_access': True,
        },
        {
            'record_id': 'SAMPLE002', 
            'title': 'Withdrawn Study on Climate Change Effects',
            'author': 'Alice Johnson; Bob Wilson',
            'journal': 'Environmental Science Review',
            'publisher': 'Academic Press',
            'original_paper_date': timezone.now().date() - datetime.timedelta(days=600),
            'retraction_date': timezone.now().date() - datetime.timedelta(days=50),
            'reason': 'Statistical errors; Methodology issues',
            'subject': 'Environmental Science; Earth Sciences',
            'country': 'United Kingdom',
            'institution': 'Cambridge Research Institute',
            'original_paper_doi': '10.1000/sample.002',
            'is_open_access': False,
        }
    ]
    
    for paper_data in sample_papers:
        RetractedPaper.objects.create(**paper_data)
    
    print(f'Created {len(sample_papers)} sample papers')
    print(f'Total papers in database: {RetractedPaper.objects.count()}')
"
```

## ⚙️ Step 7: Gunicorn Configuration

```bash
# Create Gunicorn configuration
nano gunicorn.conf.py
```

**Add to `gunicorn.conf.py`:**
```python
bind = "127.0.0.1:8001"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "xeradb"
group = "xeradb"
```

## 🔄 Step 8: Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/xeradb-prct.service
```

**Add to `/etc/systemd/system/xeradb-prct.service`:**
```ini
[Unit]
Description=Xera DB - Post-Retraction Citation Tracker (PRCT)
After=network.target postgresql.service

[Service]
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/prct
Environment="PATH=/var/www/prct/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=citing_retracted.production_settings"
Environment="XERADB_PROJECT=prct"
Environment="RAILWAY_ENVIRONMENT=production"
ExecStart=/var/www/prct/venv/bin/gunicorn --config /var/www/prct/gunicorn.conf.py citing_retracted.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable xeradb-prct
sudo systemctl start xeradb-prct
sudo systemctl status xeradb-prct
```

## 🌐 Step 9: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/prct
```

**Add to `/etc/nginx/sites-available/prct`:**
```nginx
server {
    listen 80;
    server_name prct.xeradb.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name prct.xeradb.com;

    ssl_certificate /etc/letsencrypt/live/xeradb.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xeradb.com/privkey.pem;

    client_max_body_size 100M;

    # Security headers
    include /etc/nginx/conf.d/security.conf;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/prct;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /var/www/prct;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Add ecosystem headers
        add_header X-Powered-By "Xera-DB";
        add_header X-Project "PostRetractionCitationTracker";
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/prct /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## ✅ Step 10: Final Testing & Verification

```bash
# Check all services are running
sudo systemctl status xeradb-prct
sudo systemctl status nginx
sudo systemctl status postgresql

# Check application logs
sudo journalctl -u xeradb-prct --since "5 minutes ago"

# Create environment file for the systemd service
sudo cat > /var/www/prct/.env << 'EOF'
SECRET_KEY=2QU5738Q%jW+R46#yd=ir8G5i02XSLi5_t7qpeiblUKY9X6N5V
DB_PASSWORD=!*)@&)
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
EOF







python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
print('SECRET_KEY=' + '2QU5738Q%jW+R46#yd=ir8G5i02XSLi5_t7qpeiblUKY9X6N5V')
"



# Secure the file
sudo chown xeradb:xeradb /var/www/prct/.env
sudo chmod 600 /var/www/prct/.env

# Test the application
curl -I http://prct.xeradb.com/
# Should return HTTP 200 OK

# Check database has data
sudo -u xeradb psql -h localhost -U prct_user -d prct_production -c "SELECT COUNT(*) FROM papers_retractedpaper;"
sudo -u xeradb psql -h localhost -U prct_user -d prct_production -c "SELECT title FROM papers_retractedpaper LIMIT 3;"
```

## 🎉 Deployment Complete!

Your Post-Retraction Citation Tracker is now deployed and accessible at:
- **HTTPS**: `https://prct.xeradb.com`
- **Admin**: `https://prct.xeradb.com/admin/`

### 🔧 Useful Commands for Maintenance:

```bash
# Restart PRCT application
sudo systemctl restart xeradb-prct

# Check logs
sudo journalctl -u xeradb-prct -f

# Update application
cd /var/www/prct
sudo -u xeradb git pull origin main
sudo -u xeradb bash -c "cd /var/www/prct && source venv/bin/activate && pip install -r requirements.txt"
sudo -u xeradb bash -c "cd /var/www/prct && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings && python manage.py migrate"
sudo -u xeradb bash -c "cd /var/www/prct && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings && python manage.py collectstatic --noinput"
sudo systemctl restart xeradb-prct

# Monitor resources
htop
df -h
free -h
```

## 🚨 Troubleshooting

### Common Issues:

1. **Migration fails with "permission denied for schema public"**: 
   - Run PostgreSQL permission fixes from Step 1
   - Grant superuser privileges: `sudo -u postgres psql -c "ALTER USER prct_user WITH SUPERUSER;"`

2. **Service won't start**: `sudo journalctl -u xeradb-prct`

3. **Database connection error**: Check password in `.env` file matches PostgreSQL user password

4. **Permission errors**: `sudo chown -R xeradb:xeradb /var/www/prct`

5. **502 Bad Gateway**: Check if gunicorn is running on port 8001: `sudo systemctl status xeradb-prct`

6. **Static files not loading**: Run `python manage.py collectstatic --noinput`

7. **Import commands fail**: Ensure `RAILWAY_ENVIRONMENT=production` is set

8. **Plotly charts not loading**: Check if Plotly.js CDN is accessible

## 📊 Step 11: Import Real Citation Data (When Available)

**If you have real retracted papers and citation data:**

```bash
# Transfer data from local machine (run from local terminal)
scp -r data/ xeradb@91.99.161.136:/var/www/prct/

# On VPS: Import real data
cd /var/www/prct
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
export RAILWAY_ENVIRONMENT=production

# Import retracted papers
python manage.py import_retracted_papers --file=data/retracted_papers.csv

# Import citations (create command as needed)
# python manage.py import_citations --file=data/citations.csv

# Check final database status
python manage.py shell -c "
from papers.models import RetractedPaper, Citation
print(f'📄 Total Retracted Papers: {RetractedPaper.objects.count():,}')
print(f'📈 Total Citations: {Citation.objects.count():,}')
print(f'🔥 Post-retraction Citations: {Citation.objects.filter(days_after_retraction__gt=0).count():,}')
"
```

## 🔧 Step 12: Remove Superuser Privileges (Security)

```bash
# After all imports are complete, remove superuser privileges for security
sudo -u postgres psql -c "ALTER USER prct_user WITH NOSUPERUSER;"
```

## 🔗 Step 13: Update Xera DB Ecosystem

```bash
# Add PRCT to main xeradb.com landing page
# Update /var/www/xeradb-main/index.html to include PRCT link
```

### Features Deployed:
- ✅ **Advanced Search**: With citation count filters and post-retraction filters
- ✅ **Analytics Dashboard**: Citation heatmaps, world choropleth maps, subject sunburst
- ✅ **Export Functionality**: CSV and Excel export of search results
- ✅ **Mobile Responsive**: Optimized heatmaps and layouts for mobile devices
- ✅ **Performance Optimized**: Database indexes for fast queries
- ✅ **Most Problematic Papers**: Top 3 papers with highest post-retraction citations

### Next Steps:
1. Set up DNS for `prct.xeradb.com → 91.99.161.136`
2. Import real retracted papers data
3. Set up automated citation tracking
4. Configure data update schedules
5. Add PRCT to main Xera DB ecosystem page

🎯 **Your Post-Retraction Citation Tracker is now live at `https://prct.xeradb.com`!** 

This deployment follows your established Xera DB ecosystem patterns and integrates seamlessly with your existing infrastructure on Hetzner VPS. 