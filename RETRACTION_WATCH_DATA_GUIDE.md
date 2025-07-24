# 📊 Getting Latest Retraction Watch Data

## 🎯 **Official Sources**

### **1. Retraction Watch Database (Primary)**
- **Website**: http://retractiondatabase.org/
- **Direct CSV**: http://retractiondatabase.org/RetractionWatch.csv
- **Format**: CSV with comprehensive retraction metadata
- **Update Frequency**: Regularly updated by Retraction Watch team

### **2. Alternative Sources**
- **CrossRef API**: For DOI-based retraction data
- **PubMed Retractions**: MEDLINE retraction notices
- **Manual Export**: Via Retraction Watch website interface

## 🤖 **Automated Download Options**

### **Option 1: Simple Bash Script**
```bash
# Run the provided download script
./download_retraction_watch.sh
```

### **Option 2: Python Script (Advanced)**
```bash
# Install dependencies first
pip install pandas beautifulsoup4 requests

# Run the Python fetcher
python fetch_retraction_watch_data.py
```

### **Option 3: Direct Download Commands**
```bash
# Quick download with curl
curl -L -o "retraction_watch_$(date +%Y%m%d).csv" \
  "http://retractiondatabase.org/RetractionWatch.csv"

# Or with wget
wget -O "retraction_watch_$(date +%Y%m%d).csv" \
  "http://retractiondatabase.org/RetractionWatch.csv"
```

## 🔍 **Manual Download Process**

1. **Visit**: http://retractiondatabase.org/
2. **Register**: Create free account (if required)
3. **Navigate**: Look for "Download" or "Export" section
4. **Select Format**: Choose CSV format
5. **Download**: Complete database export
6. **Verify**: Check file size and format

## 📋 **Expected Data Structure**

The Retraction Watch CSV typically contains:

| Column | Description |
|--------|-------------|
| `Record ID` | Unique identifier |
| `Title` | Paper title |
| `Author` | Author names |
| `Journal` | Publication journal |
| `Publisher` | Publisher name |
| `Country` | Author countries |
| `Article Type` | Type of publication |
| `Retraction Date` | Date of retraction |
| `Retraction DOI` | DOI of retraction notice |
| `Original Paper DOI` | DOI of original paper |
| `Reason` | Retraction reasons |
| `Subject` | Research subject areas |

## 🚀 **Import into PRCT Database**

After downloading the data:

### **1. Prepare for Import**
```bash
# Move to your PRCT directory
cd /var/www/prct

# Copy the downloaded file
cp ~/retraction_watch_YYYYMMDD.csv ./data/
```

### **2. Run Import Command**
```bash
# Using Django management command
source .env
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings
./venv/bin/python manage.py import_retraction_data data/retraction_watch_YYYYMMDD.csv
```

### **3. Verify Import**
```bash
# Check record count
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper
print(f'Total retracted papers: {RetractedPaper.objects.count()}')
print(f'Latest 5 records:')
for paper in RetractedPaper.objects.order_by('-id')[:5]:
    print(f'  - {paper.title[:50]}...')
"
```

## 🔄 **Automated Updates**

### **Set up Cron Job for Regular Updates**
```bash
# Edit crontab
crontab -e

# Add line for weekly updates (Sunday 2 AM)
0 2 * * 0 cd /var/www/prct && ./download_retraction_watch.sh && ./venv/bin/python manage.py import_retraction_data retraction_watch_*.csv
```

### **Django Management Command**
Create a management command for automated updates:

```bash
# Run this to create auto-update command
./venv/bin/python manage.py create_update_command
```

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **Download Fails**
   ```bash
   # Check if site is accessible
   curl -I http://retractiondatabase.org/
   
   # Try alternative URL
   wget --spider http://retractiondatabase.org/RetractionWatch.csv
   ```

2. **CSV Format Issues**
   ```bash
   # Check file format
   file retraction_watch_*.csv
   head -5 retraction_watch_*.csv
   
   # Count lines
   wc -l retraction_watch_*.csv
   ```

3. **Import Errors**
   ```bash
   # Check Django logs
   tail -f logs/django.log
   
   # Test import with dry-run
   ./venv/bin/python manage.py import_retraction_data --dry-run data.csv
   ```

## 📈 **Data Quality Checks**

After import, verify data quality:

```bash
# Check for duplicates
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper
from django.db.models import Count
dupes = RetractedPaper.objects.values('record_id').annotate(count=Count('id')).filter(count__gt=1)
print(f'Duplicate records: {dupes.count()}')
"

# Check date ranges
./venv/bin/python manage.py shell -c "
from papers.models import RetractedPaper
from django.db.models import Min, Max
dates = RetractedPaper.objects.aggregate(Min('retraction_date'), Max('retraction_date'))
print(f'Date range: {dates}')
"
```

## 🔗 **Alternative Data Sources**

If Retraction Watch is unavailable:

### **CrossRef API**
```bash
# Get retraction notices from CrossRef
curl "https://api.crossref.org/works?filter=type:retraction&rows=1000&mailto=your-email@example.com"
```

### **PubMed Search**
```bash
# Search for retraction notices
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=retracted+publication"
```

### **COPE Database**
- Committee on Publication Ethics retraction database
- Manual export available

## 📊 **Data Updates Schedule**

- **Retraction Watch**: Updated continuously
- **Recommended Sync**: Weekly
- **Full Refresh**: Monthly
- **Emergency Updates**: As needed for major retractions

## ✅ **Success Indicators**

After successful update:

- ✅ New retraction records imported
- ✅ No duplicate records created  
- ✅ Analytics charts show updated data
- ✅ Citation tracking includes new papers
- ✅ Database integrity maintained

Your PRCT database will now have the most current retraction data available! 🎉 