#!/bin/bash

# Simple Democracy Analysis Runner (No R Analysis Required)
# This script just imports data and updates visualizations

set -e

echo "🏛️  Simple Democracy Analysis Setup"
echo "==================================="

# Configuration
LOG_FILE="democracy_simple_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "Starting simple democracy analysis setup..."

# Check prerequisites
log_message "Checking prerequisites..."

if [[ ! -f "manage.py" ]]; then
    echo "❌ Django manage.py not found. Run this script from the project root."
    exit 1
fi

log_message "✅ Prerequisites check passed"

# Import democracy data (this works since you have the CSV file)
log_message "Importing democracy data..."

python3 manage.py import_democracy_data \
    --clear-existing \
    --update-visualizations \
    2>&1 | tee -a "$LOG_FILE"

if [[ $? -eq 0 ]]; then
    log_message "✅ Democracy data import completed successfully"
else
    log_message "❌ Democracy data import failed"
    exit 1
fi

# Run Django checks
log_message "Running Django system checks..."

python3 manage.py check 2>&1 | tee -a "$LOG_FILE"

if [[ $? -eq 0 ]]; then
    log_message "✅ Django checks passed"
else
    log_message "❌ Django checks failed"
    exit 1
fi

# Collect static files for production
if [[ "$1" == "--production" ]]; then
    log_message "Collecting static files for production..."
    
    python3 manage.py collectstatic --noinput 2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_message "✅ Static files collected"
    else
        log_message "❌ Static file collection failed"
        exit 1
    fi
    
    log_message "🔄 Restart your web server (gunicorn/apache) manually"
fi

log_message "🎉 Democracy analysis setup completed successfully!"
log_message "📊 Your democracy analysis is now available at: /democracy-analysis/"

# Show summary
echo ""
echo "📈 Analysis Summary:"
echo "==================="

python3 manage.py shell << 'EOF'
from papers.models import DemocracyData, DemocracyAnalysisResults
from django.db import models

democracy_count = DemocracyData.objects.count()
results_count = DemocracyAnalysisResults.objects.count()
countries = DemocracyData.objects.values('country').distinct().count()
years = DemocracyData.objects.aggregate(
    min_year=models.Min('year'), 
    max_year=models.Max('year')
)

print(f"• {democracy_count:,} democracy data observations")
print(f"• {countries} unique countries")
if years['min_year']:
    print(f"• {years['min_year']}-{years['max_year']} time period")
print(f"• {results_count} statistical analysis results")
print("")
print("🌐 Website sections updated:")
print("• Democracy analysis page (/democracy-analysis/)")
print("• Interactive visualizations")
print("• Statistical results tables")
print("• Methodology documentation")
EOF

echo ""
log_message "📋 Full log saved to: $LOG_FILE"