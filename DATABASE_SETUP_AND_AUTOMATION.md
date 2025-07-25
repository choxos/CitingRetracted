# PRCT Database Setup and Daily Automation Guide

This guide covers how to populate your PRCT application with real retraction data and set up automated daily updates.

## 🎯 Overview

After SSL setup, your PRCT application is live at https://prct.xeradb.com. This guide will help you:

1. **Clear sample data** from the database
2. **Import real retracted papers** from Retraction Watch
3. **Fetch citations** from academic APIs
4. **Set up automated daily updates** using Celery

## 🗂️ Step 1: Clear Sample Data

Remove any existing sample data to start fresh:

```bash
# On your server, clear existing sample data
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

# Clear existing data
./venv/bin/python manage.py shell << 'EOF'
from papers.models import RetractedPaper, CitingPaper, Citation, DataImportLog
print('Clearing existing data...')
Citation.objects.all().delete()
CitingPaper.objects.all().delete()
RetractedPaper.objects.all().delete() 
DataImportLog.objects.all().delete()
print('Sample data cleared!')
EOF
"
```

## 📥 Step 2: Import Retracted Papers from Retraction Watch

Import real retracted papers data from Retraction Watch CSV:

```bash
# Import retracted papers data
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

# Download and import retraction watch data (this will take several minutes)
echo 'Starting retracted papers import...'
./venv/bin/python manage.py import_retraction_watch --update-existing --limit 1000
"
```

### Alternative: Import from Local CSV File

If you have a local Retraction Watch CSV file:

```bash
# Upload CSV file to server first, then:
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

# Import from specific file
./venv/bin/python manage.py import_retraction_watch /path/to/retraction_watch.csv --update-existing
"
```

### Import Options

- `--update-existing`: Update existing records with new data
- `--limit N`: Process only first N rows
- `--dry-run`: Preview changes without saving to database

## 🔍 Step 3: Fetch Citations from APIs

Retrieve citation data for the imported papers:

```bash
# Fetch citations for the imported papers
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

# Fetch citations for first 50 papers (this will take 10-15 minutes)
echo 'Starting citation fetching...'
./venv/bin/python manage.py fetch_citations --limit 50
"
```

### Citation Fetch Options

- `--limit N`: Process maximum N papers
- `--paper-id ID`: Fetch citations for specific paper ID
- `--force-refresh`: Force refresh even for recently checked papers
- `--dry-run`: Preview API calls without saving data

## ⏰ Step 4: Set Up Daily Automated Updates

### 4.1 Install Redis (Required for Celery)

```bash
# Install Redis for background tasks
sudo apt update
sudo apt install redis-server

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Should return: PONG
```

### 4.2 Install Celery Dependencies

```bash
# Install Celery in your virtual environment
sudo -u xeradb bash -c "
cd /var/www/prct
./venv/bin/pip install celery[redis] django-celery-beat
"
```

### 4.3 Create Celery Configuration

```bash
# Create Celery configuration
sudo -u xeradb tee /var/www/prct/citing_retracted/celery.py > /dev/null << 'EOF'
import os
from celery import Celery
from django.conf import settings

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.production_settings')

app = Celery('citing_retracted')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'refresh-retracted-papers': {
        'task': 'papers.tasks.refresh_retracted_papers',
        'schedule': crontab(hour=13, minute=0),  # 8:00 AM EST (13:00 UTC)
    },
    'refresh-citations': {
        'task': 'papers.tasks.refresh_citations', 
        'schedule': crontab(hour=13, minute=30),  # 8:30 AM EST (13:30 UTC)
    },
    'cleanup-old-logs': {
        'task': 'papers.tasks.cleanup_old_logs',
        'schedule': crontab(hour=7, minute=0, day_of_week=0),  # Sundays 2:00 AM EST
    },
}

app.conf.timezone = 'UTC'
EOF
```

### 4.4 Update Django Settings for Celery

```bash
# Add Celery settings to production_settings.py
sudo -u xeradb tee -a /var/www/prct/citing_retracted/production_settings.py > /dev/null << 'EOF'

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Celery Beat Database Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Add django_celery_beat to installed apps
INSTALLED_APPS += ['django_celery_beat']
EOF
```

### 4.5 Create Celery Systemd Services

#### Celery Worker Service

```bash
# Create Celery worker service
sudo tee /etc/systemd/system/xeradb-prct-celery.service > /dev/null << 'EOF'
[Unit]
Description=PRCT Celery Worker
After=network.target

[Service]
Type=forking
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/prct
Environment=PATH=/var/www/prct/venv/bin
EnvironmentFile=/var/www/prct/.env
ExecStart=/var/www/prct/venv/bin/celery -A citing_retracted worker --loglevel=info --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

#### Celery Beat Scheduler Service

```bash
# Create Celery beat service  
sudo tee /etc/systemd/system/xeradb-prct-beat.service > /dev/null << 'EOF'
[Unit]
Description=PRCT Celery Beat Scheduler
After=network.target

[Service]
Type=forking
User=xeradb
Group=xeradb
WorkingDirectory=/var/www/prct
Environment=PATH=/var/www/prct/venv/bin
EnvironmentFile=/var/www/prct/.env
ExecStart=/var/www/prct/venv/bin/celery -A citing_retracted beat --loglevel=info --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

### 4.6 Run Migrations and Start Services

```bash
# Run migrations for Celery Beat
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
./venv/bin/python manage.py migrate
"

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable xeradb-prct-celery
sudo systemctl enable xeradb-prct-beat
sudo systemctl start xeradb-prct-celery
sudo systemctl start xeradb-prct-beat

# Check service status
sudo systemctl status xeradb-prct-celery
sudo systemctl status xeradb-prct-beat
```

## 📊 Step 5: Set Up Scheduled Tasks in Django Admin

```bash
# Create periodic tasks
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

./venv/bin/python manage.py shell << 'EOF'
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

# Create cron schedules
daily_8am, _ = CrontabSchedule.objects.get_or_create(
    minute=0, hour=13, day_of_week='*', day_of_month='*', month_of_year='*'
)
daily_830am, _ = CrontabSchedule.objects.get_or_create(
    minute=30, hour=13, day_of_week='*', day_of_month='*', month_of_year='*'
)
weekly_sunday, _ = CrontabSchedule.objects.get_or_create(
    minute=0, hour=7, day_of_week=0, day_of_month='*', month_of_year='*'
)

# Create periodic tasks
PeriodicTask.objects.get_or_create(
    name='Refresh Retracted Papers Daily',
    defaults={
        'crontab': daily_8am,
        'task': 'papers.tasks.refresh_retracted_papers',
    }
)

PeriodicTask.objects.get_or_create(
    name='Refresh Citations Daily', 
    defaults={
        'crontab': daily_830am,
        'task': 'papers.tasks.refresh_citations',
        'kwargs': json.dumps({'limit': 100}),
    }
)

PeriodicTask.objects.get_or_create(
    name='Cleanup Old Logs Weekly',
    defaults={
        'crontab': weekly_sunday,
        'task': 'papers.tasks.cleanup_old_logs',
    }
)

print('Scheduled tasks created successfully!')
EOF
"
```

## ✅ Step 6: Test Everything

```bash
# Test that everything is working
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

echo 'Testing database connection...'
./venv/bin/python manage.py shell -c 'from papers.models import RetractedPaper; print(f\"Papers in database: {RetractedPaper.objects.count()}\")'

echo 'Testing Celery tasks...'
./venv/bin/python manage.py shell -c 'from papers.tasks import refresh_retracted_papers; result = refresh_retracted_papers.delay(); print(f\"Task submitted: {result.id}\")'
"

# Check all services are running
sudo systemctl status xeradb-prct
sudo systemctl status xeradb-prct-celery  
sudo systemctl status xeradb-prct-beat
sudo systemctl status redis-server

# Test your website
curl -I https://prct.xeradb.com
```

## 📋 Daily Schedule Summary

Your PRCT application will now automatically:

- **Daily at 8:00 AM EST (1:00 PM UTC)**: Download latest retracted papers from Retraction Watch
- **Daily at 8:30 AM EST (1:30 PM UTC)**: Fetch citations for up to 100 papers from academic APIs  
- **Weekly on Sundays at 2:00 AM EST (7:00 AM UTC)**: Clean up old log files

## 🎛️ Available Management Commands

### Retracted Papers Import

```bash
# Import from CSV file
./venv/bin/python manage.py import_retraction_watch /path/to/file.csv

# Import with options
./venv/bin/python manage.py import_retraction_watch file.csv --update-existing --limit 500

# Dry run to preview
./venv/bin/python manage.py import_retraction_watch file.csv --dry-run
```

### Citation Fetching

```bash
# Fetch citations for all papers needing updates
./venv/bin/python manage.py fetch_citations

# Fetch for specific paper
./venv/bin/python manage.py fetch_citations --paper-id RW12345

# Fetch with limits and force refresh
./venv/bin/python manage.py fetch_citations --limit 25 --force-refresh

# Dry run to see what would be processed
./venv/bin/python manage.py fetch_citations --dry-run --limit 10
```

### Data Maintenance

```bash
# Clean up old import logs
./venv/bin/python manage.py cleanup_old_logs

# Fix citation date calculations
./venv/bin/python manage.py fix_citation_dates

# Clean institution names
./venv/bin/python manage.py clean_institution_names

# Populate subject fields
./venv/bin/python manage.py populate_subject_fields
```

## 📊 Monitoring and Management

### Service Status

```bash
# Check all PRCT services
sudo systemctl status xeradb-prct          # Main web application
sudo systemctl status xeradb-prct-celery   # Background worker
sudo systemctl status xeradb-prct-beat     # Task scheduler
sudo systemctl status redis-server         # Message broker

# View service logs
sudo journalctl -u xeradb-prct-celery -f   # Worker logs
sudo journalctl -u xeradb-prct-beat -f     # Scheduler logs
```

### Django Admin Interface

- **Scheduled Tasks**: Visit https://prct.xeradb.com/admin/django_celery_beat/
- **Task Management**: View and modify periodic tasks
- **Task History**: Monitor execution results
- **Cron Schedules**: Configure custom schedules

### Redis Status

```bash
# Test Redis connection
redis-cli ping

# View Redis info
redis-cli info

# Monitor Redis activity
redis-cli monitor
```

### Manual Task Execution

```bash
# Run tasks manually via Django shell
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DB_PASSWORD='$(grep DB_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

./venv/bin/python manage.py shell << 'EOF'
from papers.tasks import refresh_retracted_papers, refresh_citations, cleanup_old_logs

# Run tasks immediately
print('Running retracted papers refresh...')
result1 = refresh_retracted_papers.delay()
print(f'Task ID: {result1.id}')

print('Running citations refresh...')
result2 = refresh_citations.delay()
print(f'Task ID: {result2.id}')

print('Tasks submitted successfully!')
EOF
"
```

## 🚨 Troubleshooting

### Common Issues

1. **Celery services not starting**
   ```bash
   # Check logs
   sudo journalctl -u xeradb-prct-celery --no-pager
   
   # Restart services
   sudo systemctl restart xeradb-prct-celery
   sudo systemctl restart xeradb-prct-beat
   ```

2. **Redis connection errors**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Test connection
   redis-cli ping
   
   # Restart Redis
   sudo systemctl restart redis-server
   ```

3. **Import command fails**
   ```bash
   # Check Django settings
   echo $DJANGO_SETTINGS_MODULE
   
   # Test database connection
   ./venv/bin/python manage.py check --deploy
   
   # Run with verbose output
   ./venv/bin/python manage.py import_retraction_watch file.csv --verbosity 2
   ```

4. **Tasks not running on schedule**
   ```bash
   # Check beat scheduler logs
   sudo journalctl -u xeradb-prct-beat --no-pager
   
   # Verify tasks in Django admin
   # Visit: https://prct.xeradb.com/admin/django_celery_beat/periodictask/
   ```

### Performance Optimization

1. **Increase worker processes**
   ```bash
   # Edit the celery service file
   sudo nano /etc/systemd/system/xeradb-prct-celery.service
   
   # Change ExecStart line to:
   # ExecStart=/var/www/prct/venv/bin/celery -A citing_retracted worker --loglevel=info --concurrency=4 --detach
   ```

2. **Optimize API rate limits**
   ```bash
   # Edit production settings
   sudo nano /var/www/prct/citing_retracted/production_settings.py
   
   # Adjust rate limits based on your API quotas
   ```

## 🎯 Next Steps

1. **Monitor daily updates** for the first week to ensure smooth operation
2. **Set up log rotation** to manage disk space
3. **Configure monitoring alerts** for failed tasks
4. **Scale worker processes** based on workload
5. **Set up database backups** for production data

Your PRCT application is now fully automated and ready for production use! 🚀

## 📚 Additional Resources

- **Django Management Commands**: See `management_commands.md` for detailed command documentation
- **Celery Documentation**: [docs.celeryproject.org](https://docs.celeryproject.org/)
- **Django-Celery-Beat**: [django-celery-beat.readthedocs.io](https://django-celery-beat.readthedocs.io/)
- **Redis Documentation**: [redis.io/documentation](https://redis.io/documentation) 