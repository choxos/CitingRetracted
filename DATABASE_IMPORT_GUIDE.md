# 📊 Import Retraction Watch Data into PRCT Database

## 🎯 **Three Ways to Update Your Database**

### **Option 1: Automated Pipeline (Recommended)**
```bash
# Complete automation - download + import + citations
python update_retraction_database.py

# Test run without making changes
python update_retraction_database.py --dry-run

# Custom installation path
python update_retraction_database.py --prct-path /var/www/prct

# Download only (no import)
python update_retraction_database.py --download-only
```

### **Option 2: Using Existing Management Commands**
```bash
# 1. Download data first
./download_retraction_watch.sh

# 2. Import into database
cd /var/www/prct
source .env
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

./venv/bin/python manage.py import_retraction_watch retraction_watch_YYYYMMDD.csv

# 3. Optional: Fetch citations
./venv/bin/python manage.py fetch_citations --limit 100
```

### **Option 3: Manual Process**
```bash
# 1. Manual download
curl -L -o "retraction_watch_$(date +%Y%m%d).csv" \
  "http://retractiondatabase.org/RetractionWatch.csv"

# 2. Test import (dry run)
./venv/bin/python manage.py import_retraction_watch \
  --dry-run retraction_watch_YYYYMMDD.csv

# 3. Real import
./venv/bin/python manage.py import_retraction_watch \
  --update-existing retraction_watch_YYYYMMDD.csv
```

## 🚀 **Quick Start for Your VPS**

### **Deploy the New Tools:**
```bash
# SSH to your VPS
ssh xeradb@91.99.161.136
cd /var/www/prct

# Pull the latest tools
git pull origin main

# Make scripts executable
chmod +x update_retraction_database.py
chmod +x download_retraction_watch.sh

# Install Python dependencies (if needed)
./venv/bin/pip install beautifulsoup4 requests
```

### **Run First Update:**
```bash
# Test the pipeline (dry run)
python update_retraction_database.py --dry-run

# Run the real update
python update_retraction_database.py

# Check results
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper
print(f'Total papers: {RetractedPaper.objects.count():,}')
print(f'Latest 3: {[p.title[:50] for p in RetractedPaper.objects.order_by(\"-id\")[:3]]}')
"
```

## 🔧 **Management Command Options**

### **Import Retraction Watch Data:**
```bash
# Basic import
./venv/bin/python manage.py import_retraction_watch data.csv

# With options
./venv/bin/python manage.py import_retraction_watch data.csv \
  --dry-run \                    # Preview without saving
  --update-existing \            # Update existing records
  --limit 1000                   # Process only first 1000 rows
```

### **Fetch Citations:**
```bash
# Fetch citations for all papers
./venv/bin/python manage.py fetch_citations

# With options
./venv/bin/python manage.py fetch_citations \
  --paper-id RW12345 \          # Specific paper
  --limit 50 \                  # Process 50 papers
  --force-refresh \             # Re-fetch even recent ones
  --api openalex                # Use specific API
```

### **Data Cleanup Commands:**
```bash
# Fix citation date calculations
./venv/bin/python manage.py fix_citation_dates

# Clean up country data
./venv/bin/python manage.py clean_country_data

# Populate subject fields
./venv/bin/python manage.py populate_subject_fields

# Clean institution names
./venv/bin/python manage.py clean_institution_names
```

## 📊 **Expected Data Structure**

Your CSV should have these columns:
```
Record ID, Title, Author, Journal, Publisher, Institution, Country, 
ArticleType, Subject, OriginalPaperDOI, RetractionDOI, URLS, 
OriginalPaperPubMedID, RetractionPubMedID, RetractionNature, 
Reason, Notes, Paywalled, OriginalPaperDate, RetractionDate
```

## ⚙️ **Automated Updates**

### **Set up Cron Job for Weekly Updates:**
```bash
# Edit crontab
crontab -e

# Add weekly update (Sundays at 2 AM)
0 2 * * 0 cd /var/www/prct && python update_retraction_database.py >> logs/update.log 2>&1
```

### **Systemd Service for Updates:**
```bash
# Create service file
sudo tee /etc/systemd/system/prct-update.service << 'EOF'
[Unit]
Description=PRCT Database Update
After=network.target

[Service]
Type=oneshot
User=xeradb
WorkingDirectory=/var/www/prct
ExecStart=/var/www/prct/venv/bin/python update_retraction_database.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create timer
sudo tee /etc/systemd/system/prct-update.timer << 'EOF'
[Unit]
Description=Run PRCT update weekly
Requires=prct-update.service

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable prct-update.timer
sudo systemctl start prct-update.timer
```

## 🔍 **Monitoring and Verification**

### **Check Import Logs:**
```bash
# View Django logs
./venv/bin/python manage.py shell -c "
from papers.models import DataImportLog
for log in DataImportLog.objects.order_by('-start_time')[:5]:
    print(f'{log.start_time}: {log.import_type} - {log.status}')
    print(f'  Processed: {log.records_processed}, Created: {log.records_created}')
"
```

### **Database Statistics:**
```bash
# Quick stats
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper, Citation
from django.db.models import Count
print(f'📊 PRCT Database Statistics:')
print(f'   Total retracted papers: {RetractedPaper.objects.count():,}')
print(f'   Total citations: {Citation.objects.count():,}')
print(f'   Post-retraction citations: {Citation.objects.filter(days_after_retraction__gt=0).count():,}')
print(f'   Papers with DOIs: {RetractedPaper.objects.exclude(original_paper_doi=\"\").count():,}')
print(f'   Papers by year (recent):')
for year_data in RetractedPaper.objects.filter(retraction_date__year__gte=2020).values('retraction_date__year').annotate(count=Count('id')).order_by('-retraction_date__year')[:5]:
    print(f'     {year_data[\"retraction_date__year\"]}: {year_data[\"count\"]:,} retractions')
"
```

### **Check for Issues:**
```bash
# Find potential data issues
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper
print('🔍 Data Quality Check:')

# Missing critical fields
missing_titles = RetractedPaper.objects.filter(title='').count()
missing_journals = RetractedPaper.objects.filter(journal='').count()
missing_dates = RetractedPaper.objects.filter(retraction_date__isnull=True).count()

print(f'   Missing titles: {missing_titles}')
print(f'   Missing journals: {missing_journals}') 
print(f'   Missing retraction dates: {missing_dates}')

# Duplicates
from django.db.models import Count
dupes = RetractedPaper.objects.values('record_id').annotate(count=Count('id')).filter(count__gt=1).count()
print(f'   Duplicate record IDs: {dupes}')
"
```

## 🛠️ **Troubleshooting**

### **Common Import Issues:**

1. **Permission Errors:**
```bash
# Fix permissions
sudo chown -R xeradb:xeradb /var/www/prct/data/
chmod 755 /var/www/prct/data/
```

2. **Database Connection Issues:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
./venv/bin/python manage.py dbshell
```

3. **CSV Format Issues:**
```bash
# Check file encoding
file retraction_watch_*.csv

# Check headers
head -1 retraction_watch_*.csv

# Count lines
wc -l retraction_watch_*.csv
```

4. **Memory Issues:**
```bash
# Import in batches
./venv/bin/python manage.py import_retraction_watch \
  --limit 1000 data.csv

# Check memory usage
free -h
```

## 📈 **Performance Tips**

### **Large Dataset Imports:**
```bash
# Use batch processing
./venv/bin/python manage.py import_retraction_watch \
  --limit 5000 \
  --update-existing \
  data.csv

# Monitor progress
tail -f logs/django.log
```

### **Citation Fetching Optimization:**
```bash
# Fetch citations in small batches
./venv/bin/python manage.py fetch_citations --limit 50

# Use specific paper if needed
./venv/bin/python manage.py fetch_citations --paper-id RW12345
```

## ✅ **Success Indicators**

After successful import:

- ✅ **No import errors** in Django logs
- ✅ **Record counts increased** appropriately  
- ✅ **Analytics charts show new data**
- ✅ **Recent retractions appear** in admin
- ✅ **Citation fetching works** for new papers
- ✅ **Database integrity maintained**

## 🎯 **Next Steps**

1. **Deploy the tools** to your VPS
2. **Run initial update** with `--dry-run` first
3. **Execute real import** once verified
4. **Set up automated updates** with cron/systemd
5. **Monitor logs** for ongoing health
6. **Check analytics** for data visualization

Your PRCT database will stay current with the latest retraction data! 🚀 