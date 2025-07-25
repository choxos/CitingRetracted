# 🚀 PRCT VPS Deployment Guide with XeraDB Theme

## 📋 Overview

This guide will help you deploy the Post-Retraction Citation Tracker (PRCT) with the new XeraDB theme to your VPS using your existing PostgreSQL database (`prct_production`).

## 🏗️ Prerequisites

- ✅ VPS with Ubuntu/Debian
- ✅ PostgreSQL database: `prct_production`
- ✅ Domain name (optional)
- ✅ SSH access to VPS
- ✅ Git installed on VPS

## 📦 Step 1: Preparation

### 1.1 Push Latest Changes to GitHub

```bash
# On your local machine, ensure all changes are committed
git add .
git commit -m "Final XeraDB theme migration with analytics fixes"
git push origin main
```

### 1.2 Connect to Your VPS

```bash
ssh your_username@your_vps_ip
```

## 🔄 Step 2: Update Application Code

### 2.1 Navigate to Application Directory

```bash
cd /path/to/your/prct/application
# or if it's in your home directory:
cd ~/CitingRetracted
```

### 2.2 Pull Latest Changes

```bash
# Backup current state (optional)
git stash

# Pull latest changes
git pull origin main

# If you had local changes, restore them
# git stash pop
```

## 🗄️ Step 3: Database Configuration

### 3.1 Verify PostgreSQL Connection

```bash
# Test connection to your existing database
sudo -u postgres psql -c "\l" | grep prct_production
```

### 3.2 Update Django Settings

Create or update your production settings:

```bash
# Create production settings file
nano citing_retracted/settings_production.py
```

Add the following content:

```python
from .settings import *
import os

# Production settings
DEBUG = False

ALLOWED_HOSTS = [
    'prct.xeradb.com',
    'www.prctxeradb.com', 
    '91.99.161.136',
    'localhost',
    '127.0.0.1'
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prct_production',
        'USER': 'prct_user',
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = '/var/www/prct/static/'
STATIC_URL = '/static/'

# Media files  
MEDIA_ROOT = '/var/www/prct/media/'
MEDIA_URL = '/media/'

# Security settings
SECURE_SSL_REDIRECT = True  # Set to True if using HTTPS
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF protection
CSRF_TRUSTED_ORIGINS = [
    'https://prct.xeradb.com',
    'https://www.prctxeradb.com',
    'http://91.99.161.136:8000'
]

# Performance
USE_TZ = True
TIME_ZONE = 'UTC'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/prct/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 3.3 Set Environment Variables

```bash
# Create environment file
nano ~/.bashrc

# Add these lines at the end:
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production
export SECRET_KEY='2QU5738Q%jW+R46#yd=ir8G5i02XSLi5_t7qpeiblUKY9X6N5V'
export DATABASE_PASSWORD='Choxos102030'

# Reload environment
source ~/.bashrc
```

## 🐍 Step 4: Python Environment Setup

### 4.1 Update Virtual Environment

```bash
# Activate virtual environment
source venv/bin/activate

# or if using conda:
# conda activate prct

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production-specific packages
pip install gunicorn psycopg2-binary
```

### 4.2 Update Requirements (if needed)

```bash
# Generate updated requirements
pip freeze > requirements.txt
```

## 🔧 Step 5: Django Configuration

### 5.1 Create Required Directories

```bash
# Create static files and log directories
sudo mkdir -p /var/www/prct/static
sudo mkdir -p /var/www/prct/media
sudo mkdir -p /var/log/prct
sudo chown -R $USER:$USER /var/www/prct
sudo chown -R $USER:$USER /var/log/prct
```

### 5.2 Run Database Migrations

```bash
# Test database connection
python manage.py dbshell --settings=citing_retracted.settings_production
# Type \q to exit

# Run migrations
python manage.py migrate --settings=citing_retracted.settings_production

# Check for any migration issues
python manage.py showmigrations --settings=citing_retracted.settings_production
```

### 5.3 Collect Static Files

```bash
# Collect static files (XeraDB theme files)
python manage.py collectstatic --noinput --settings=citing_retracted.settings_production
```

### 5.4 Test Application

```bash
# Run development server to test
python manage.py runserver 0.0.0.0:8000 --settings=citing_retracted.settings_production

# Test in another terminal:
curl http://localhost:8000/

# Stop the test server with Ctrl+C
```

## 🔥 Step 6: Gunicorn Configuration

### 6.1 Create Gunicorn Configuration

```bash
nano gunicorn_config.py
```

Add:

```python
# Gunicorn configuration file
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
user = "your_username"
group = "your_username"
tmp_upload_dir = None
errorlog = "/var/log/prct/gunicorn_error.log"
accesslog = "/var/log/prct/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "info"
```

### 6.2 Create Log Directory

```bash
sudo mkdir -p /var/log/prct
sudo chown -R $USER:$USER /var/log/prct
```

### 6.3 Test Gunicorn

```bash
# Test Gunicorn
gunicorn --config gunicorn_config.py citing_retracted.wsgi:application

# Test in another terminal:
curl http://localhost:8000/

# Stop with Ctrl+C
```

## 🔧 Step 7: Systemd Service Configuration

### 7.1 Create Systemd Service File

```bash
sudo nano /etc/systemd/system/prct-gunicorn.service
```

Add:

```ini
[Unit]
Description=PRCT Gunicorn daemon
Requires=prct-gunicorn.socket
After=network.target

[Service]
Type=notify
User=your_username
Group=your_username
RuntimeDirectory=prct
WorkingDirectory=/path/to/your/prct
Environment="DJANGO_SETTINGS_MODULE=citing_retracted.settings_production"
Environment="SECRET_KEY=your-super-secret-key-here"
Environment="DATABASE_PASSWORD=your-postgres-password"
ExecStart=/path/to/your/prct/venv/bin/gunicorn \
    --config /path/to/your/prct/gunicorn_config.py \
    citing_retracted.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.2 Create Socket File

```bash
sudo nano /etc/systemd/system/prct-gunicorn.socket
```

Add:

```ini
[Unit]
Description=PRCT Gunicorn socket

[Socket]
ListenStream=/run/prct.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```

### 7.3 Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable prct-gunicorn.socket
sudo systemctl enable prct-gunicorn.service

# Start socket
sudo systemctl start prct-gunicorn.socket

# Check status
sudo systemctl status prct-gunicorn.socket
sudo systemctl status prct-gunicorn.service
```

## 🌐 Step 8: Nginx Configuration

### 8.1 Install Nginx (if not installed)

```bash
sudo apt update
sudo apt install nginx
```

### 8.2 Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/prct
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com your_vps_ip;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Static files (XeraDB theme)
    location /static/ {
        alias /var/www/prct/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/prct/media/;
        expires 7d;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Security
    location ~ /\.ht {
        deny all;
    }
    
    # Favicon
    location = /favicon.ico {
        alias /var/www/prct/static/images/favicon.ico;
        log_not_found off;
        access_log off;
    }
}
```

### 8.3 Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/prct /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🧪 Step 9: Testing Deployment

### 9.1 Test Services

```bash
# Check all services
sudo systemctl status prct-gunicorn.service
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
sudo journalctl -u prct-gunicorn.service -f
tail -f /var/log/prct/gunicorn_error.log
tail -f /var/log/nginx/error.log
```

### 9.2 Test Web Application

```bash
# Test local connection
curl -I http://localhost/

# Test your sample data
curl http://localhost/analytics/

# Test search functionality  
curl "http://localhost/search/?q=cancer"
```

### 9.3 Load Your Sample Data

```bash
# Load the sample data you created
python manage.py load_sample_data --papers 25 --citations-per-paper 12 --clear --settings=citing_retracted.settings_production
```

## 🔒 Step 10: Security & SSL (Optional)

### 10.1 Install Certbot for HTTPS

```bash
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🔧 Step 11: Maintenance Commands

### 11.1 Common Operations

```bash
# Restart application
sudo systemctl restart prct-gunicorn.service

# Update application
git pull origin main
python manage.py migrate --settings=citing_retracted.settings_production
python manage.py collectstatic --noinput --settings=citing_retracted.settings_production
sudo systemctl restart prct-gunicorn.service

# View logs
sudo journalctl -u prct-gunicorn.service -f
tail -f /var/log/prct/gunicorn_error.log

# Database backup
pg_dump prct_production > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 11.2 Monitoring Script

Create a monitoring script:

```bash
nano monitor_prct.sh
```

Add:

```bash
#!/bin/bash
echo "=== PRCT Status Check ==="
echo "Gunicorn Service:"
sudo systemctl is-active prct-gunicorn.service
echo "Nginx Service:"
sudo systemctl is-active nginx
echo "PostgreSQL Service:"
sudo systemctl is-active postgresql
echo "Web Response:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/
echo ""
echo "Disk Usage:"
df -h /var/www/prct
echo "Memory Usage:"
free -h
```

```bash
chmod +x monitor_prct.sh
```

## 🎯 Step 12: Verify XeraDB Theme Deployment

### 12.1 Test Theme Features

1. **Visit your site**: `http://your-domain.com` or `http://your_vps_ip`
2. **Check XeraDB styling**: Header, navigation, cards should use XeraDB theme
3. **Test search**: Use the header search bar
4. **Analytics page**: Visit `/analytics/` - all charts should be properly sized
5. **Sample data**: Verify 25 sample papers with citations are visible

### 12.2 Theme-Specific Verification

```bash
# Verify XeraDB theme files are served
curl -I http://localhost/static/css/xera-unified-theme.css
curl -I http://localhost/static/css/themes/prct-theme.css

# Check if static files are properly collected
ls -la /var/www/prct/static/css/
ls -la /var/www/prct/static/css/themes/
```

## 🚨 Troubleshooting

### Common Issues

1. **Static files not loading**:
   ```bash
   python manage.py collectstatic --noinput --settings=citing_retracted.settings_production
   sudo systemctl restart nginx
   ```

2. **Database connection errors**:
   ```bash
   sudo -u postgres psql -c "\l" | grep prct_production
   python manage.py dbshell --settings=citing_retracted.settings_production
   ```

3. **Permission errors**:
   ```bash
   sudo chown -R $USER:$USER /var/www/prct
   sudo chown -R www-data:www-data /var/www/prct/static
   ```

4. **Gunicorn not starting**:
   ```bash
   sudo journalctl -u prct-gunicorn.service -f
   /path/to/venv/bin/gunicorn --config gunicorn_config.py citing_retracted.wsgi:application
   ```

## ✅ Success Checklist

- [ ] Git repository updated and pulled
- [ ] PostgreSQL `prct_production` database connected
- [ ] Virtual environment activated and dependencies installed
- [ ] Django migrations completed
- [ ] Static files collected (XeraDB theme files)
- [ ] Gunicorn service running
- [ ] Nginx configured and running
- [ ] Sample data loaded (25 papers, ~300 citations)
- [ ] XeraDB theme displaying correctly
- [ ] Analytics charts properly sized and positioned
- [ ] Header search functionality working
- [ ] All URLs responding correctly

## 🎉 Congratulations!

Your PRCT application with the XeraDB theme is now deployed on your VPS using your existing PostgreSQL database. The application features:

- ✅ **Modern XeraDB Theme**: Unified design across all pages
- ✅ **Responsive Analytics**: 12+ charts with proper sizing
- ✅ **Header Search**: Integrated search functionality
- ✅ **Sample Data**: Ready for testing and demonstration
- ✅ **Production Ready**: Gunicorn + Nginx + PostgreSQL stack

**Access your application**: `http://your-domain.com` or `http://your_vps_ip`

---

**Need help?** Check the troubleshooting section or review the log files for specific error messages. 