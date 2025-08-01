# PRCT Database Setup and Daily Automation Guide

This guide covers how to set up automated daily updates for your PRCT application with real retraction data from Retraction Watch and citations from OpenCitations.

## 🎯 Overview

After SSL setup, your PRCT application is live at https://prct.xeradb.com. This guide will help you:

1. **Set up complete automation** for data updates
2. **Configure daily automated updates** using a single script
3. **Manage data cleanup** and cache clearing
4. **Monitor the automation** process

## 🤖 Complete Automation Setup

### Step 1: Download the Automation Script

```bash
# Copy the automation script to your server
cd /var/www/prct
wget https://raw.githubusercontent.com/YOUR_USERNAME/CitingRetracted/main/prct_auto_updater.py
chmod +x prct_auto_updater.py

# Install required Python packages
./venv/bin/pip install requests
```

### Step 2: Test the Automation Script

```bash
# Test the complete automation process
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DATABASE_PASSWORD='$(grep DATABASE_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production

# Run a test with limited records
./venv/bin/python prct_auto_updater.py --citation-limit 50 --import-limit 1000
"
```

### Step 3: Set Up Daily Automation

```bash
# Create crontab entry for daily updates
sudo -u xeradb crontab -e

# Add this line for daily updates at 6:00 AM
0 6 * * * cd /var/www/prct && ./venv/bin/python prct_auto_updater.py --citation-limit 100 >> logs/cron.log 2>&1
```

## 🔧 Automation Script Features

### **Complete Data Pipeline:**
- ✅ **Downloads latest Retraction Watch CSV** from official GitLab source
- ✅ **Automatically cleans up old CSV files** (keeps only latest)
- ✅ **Imports only new retraction records** (skips existing for efficiency)
- ✅ **Fetches citations from OpenCitations** for retracted papers
- ✅ **Clears analytics cache** to show updated data
- ✅ **Comprehensive logging** with timestamps

### **Smart File Management:**
- Downloads to `/var/www/prct/data/retraction_watch_YYYYMMDD_HHMMSS.csv`
- Automatically removes previous CSV files when new ones are downloaded
- Keeps only the most recent dataset to save disk space

### **Efficient Processing:**
- Only processes records with Record ID higher than existing maximum
- Eliminates duplicate key violations
- Dramatically faster imports for incremental updates

## 📊 Script Usage Options

### Basic Daily Update
```bash
# Standard daily update (recommended for cron)
./venv/bin/python prct_auto_updater.py --citation-limit 100
```

### Manual Updates with Options
```bash
# Force new download even if recent file exists
./venv/bin/python prct_auto_updater.py --force-download

# Limit imports for testing
./venv/bin/python prct_auto_updater.py --import-limit 500 --citation-limit 25

# Clean up old files only
./venv/bin/python prct_auto_updater.py --cleanup-only
```

### Advanced Configuration
```bash
# Custom PRCT path and limits
./venv/bin/python prct_auto_updater.py \
  --prct-path /custom/path/to/prct \
  --citation-limit 200 \
  --import-limit 2000
```

## 🗂️ Data Management

### Automatic Cleanup
The script automatically:
- Downloads new Retraction Watch data daily
- Removes previous CSV files after successful import
- Keeps only the latest dataset
- Maintains logs in `/var/www/prct/logs/auto_updater.log`

### Manual Data Management
```bash
# View current data files
ls -la /var/www/prct/data/retraction_watch_*.csv

# Check automation logs
tail -f /var/www/prct/logs/auto_updater.log

# Manual cleanup of old files
./venv/bin/python prct_auto_updater.py --cleanup-only
```

## 🔄 Removing Previous Citation Data

### Complete Citation Data Removal

**⚠️ Warning:** This will remove ALL citation data. Use with caution!

```bash
# Method 1: Using Django shell (Recommended)
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DATABASE_PASSWORD='$(grep DATABASE_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production

./venv/bin/python manage.py shell << 'EOF'
from papers.models import Citation, CitingPaper
print('Current citation count:', Citation.objects.count())
print('Current citing paper count:', CitingPaper.objects.count())

# Remove all citations
Citation.objects.all().delete()
print('✅ All citations removed')

# Remove all citing papers  
CitingPaper.objects.all().delete()
print('✅ All citing papers removed')

# Reset citation counts on retracted papers
from papers.models import RetractedPaper
RetractedPaper.objects.all().update(citation_count=0, last_citation_check=None)
print('✅ Citation counts reset on retracted papers')
EOF
"
```

### Selective Citation Data Removal

```bash
# Remove citations older than specific date
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DATABASE_PASSWORD='$(grep DATABASE_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production

./venv/bin/python manage.py shell << 'EOF'
from papers.models import Citation
from django.utils import timezone
from datetime import timedelta

# Remove citations older than 30 days
cutoff_date = timezone.now() - timedelta(days=30)
old_citations = Citation.objects.filter(created_at__lt=cutoff_date)
count = old_citations.count()
old_citations.delete()
print(f'✅ Removed {count} old citations')
EOF
"
```

### Reset Citation Fetch Status

```bash
# Reset citation fetch status to refetch all citations
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DATABASE_PASSWORD='$(grep DATABASE_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production

./venv/bin/python manage.py shell << 'EOF'
from papers.models import RetractedPaper

# Reset last citation check to force refetch
updated = RetractedPaper.objects.update(last_citation_check=None)
print(f'✅ Reset citation check status for {updated} papers')
print('Next citation fetch will process all papers again')
EOF
"
```

## 📋 Monitoring and Logs

### Log Files
- **Main automation log**: `/var/www/prct/logs/auto_updater.log`
- **Cron execution log**: `/var/www/prct/logs/cron.log`  
- **Django application logs**: `/var/www/prct/logs/`

### Monitoring Commands
```bash
# Check automation logs
tail -f /var/www/prct/logs/auto_updater.log

# Check cron execution
tail -f /var/www/prct/logs/cron.log

# Check database record counts
sudo -u xeradb bash -c "
cd /var/www/prct
export SECRET_KEY='$(grep SECRET_KEY .env | cut -d= -f2)'
export DATABASE_PASSWORD='$(grep DATABASE_PASSWORD .env | cut -d= -f2)'
export DJANGO_SETTINGS_MODULE=citing_retracted.settings_production

./venv/bin/python manage.py shell -c '
from papers.models import RetractedPaper, Citation, CitingPaper
print(f\"Retracted Papers: {RetractedPaper.objects.count():,}\")
print(f\"Citations: {Citation.objects.count():,}\")
print(f\"Citing Papers: {CitingPaper.objects.count():,}\")
'
"
```

### Health Check Script
```bash
# Create a simple health check script
cat > /var/www/prct/health_check.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Check if automation has run recently
log_file = Path("/var/www/prct/logs/auto_updater.log")
if log_file.exists():
    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
    if datetime.now() - mtime < timedelta(days=2):
        print(f"✅ Automation running normally (last update: {mtime})")
        sys.exit(0)
    else:
        print(f"⚠️  Last automation run: {mtime} (over 2 days ago)")
        sys.exit(1)
else:
    print("❌ No automation log found")
    sys.exit(1)
EOF

chmod +x /var/www/prct/health_check.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Automation script fails to download**
   ```bash
   # Check internet connectivity
   curl -I https://gitlab.com/crossref/retraction-watch-data/
   
   # Check disk space
   df -h /var/www/prct/data/
   
   # Check permissions
   ls -la /var/www/prct/data/
   ```

2. **Import fails with permission errors**
   ```bash
   # Fix permissions
   sudo chown -R xeradb:xeradb /var/www/prct/data/
   sudo chown -R xeradb:xeradb /var/www/prct/logs/
   ```

3. **Citation fetching times out**
   ```bash
   # Reduce citation limit in automation
   ./venv/bin/python prct_auto_updater.py --citation-limit 50
   ```

4. **Cron job not running**
   ```bash
   # Check cron service
   sudo systemctl status cron
   
   # Check user crontab
   sudo -u xeradb crontab -l
   
   # Test cron job manually
   sudo -u xeradb bash -c "cd /var/www/prct && ./venv/bin/python prct_auto_updater.py"
   ```

## 📈 Performance Optimization

### Adjust Automation Frequency
```bash
# Daily at 6 AM (recommended)
0 6 * * * cd /var/www/prct && ./venv/bin/python prct_auto_updater.py --citation-limit 100

# Every 12 hours
0 6,18 * * * cd /var/www/prct && ./venv/bin/python prct_auto_updater.py --citation-limit 50

# Weekly only (Sundays at 6 AM)
0 6 * * 0 cd /var/www/prct && ./venv/bin/python prct_auto_updater.py --citation-limit 200
```

### Resource Management
```bash
# Monitor resource usage during automation
top -u xeradb

# Check database size
sudo -u postgres psql -c "\l+ prct_production"

# Optimize database (run weekly)
sudo -u xeradb bash -c "
cd /var/www/prct
./venv/bin/python manage.py shell -c 'from django.db import connection; connection.cursor().execute(\"VACUUM ANALYZE\")'
"
```

## 🎯 Summary

Your PRCT application now has **complete automation** with:

- ✅ **Daily Retraction Watch data updates**
- ✅ **Automatic OpenCitations citation fetching**
- ✅ **Smart file management and cleanup**
- ✅ **Comprehensive logging and monitoring**
- ✅ **Easy citation data management**
- ✅ **Performance optimizations**

The automation runs seamlessly in the background, keeping your research data current and comprehensive! 🚀

## 📚 Additional Resources

- **Retraction Watch Database**: [GitLab Repository](https://gitlab.com/crossref/retraction-watch-data/)
- **OpenCitations API**: [Documentation](https://opencitations.net/index/api/v1)
- **Cron Job Tutorial**: [Linux Crontab Guide](https://www.cyberciti.biz/faq/how-do-i-add-jobs-to-cron-under-linux-or-unix-oses/)
- **Django Management Commands**: See `management_commands.md` for detailed command documentation 