#!/bin/bash

# Democracy and Retractions Analysis Runner
# This script runs the complete democracy analysis pipeline on the VPS

set -e  # Exit on any error

echo "🏛️  Democracy and Retractions Analysis Pipeline"
echo "=============================================="

# Configuration
DJANGO_PROJECT_DIR="$(pwd)"
R_ANALYSIS_DIR="../retractions_democracy"
LOG_FILE="democracy_analysis_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log_message "Checking prerequisites..."
    
    # Check if Python virtual environment is activated
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "⚠️  Warning: No virtual environment detected. Consider activating one."
    fi
    
    # Check if R is installed
    if ! command -v R &> /dev/null; then
        echo "❌ R is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Django project exists
    if [[ ! -f "manage.py" ]]; then
        echo "❌ Django manage.py not found. Run this script from the project root."
        exit 1
    fi
    
    # Check if R analysis directory exists
    if [[ ! -d "$R_ANALYSIS_DIR" ]]; then
        echo "❌ R analysis directory not found: $R_ANALYSIS_DIR"
        exit 1
    fi
    
    log_message "✅ Prerequisites check passed"
}

# Function to run Django data import
run_django_import() {
    log_message "Running Django democracy data import..."
    
    python3 manage.py import_democracy_data \
        --data-path "$R_ANALYSIS_DIR" \
        --update-visualizations \
        2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_message "✅ Django data import completed successfully"
    else
        log_message "❌ Django data import failed"
        exit 1
    fi
}

# Function to run R analysis (optional)
run_r_analysis() {
    log_message "Running R statistical analysis..."
    
    # Create output directory if it doesn't exist
    mkdir -p "./r_analysis_output"
    
    # Check if R analysis directory exists
    if [[ ! -d "$R_ANALYSIS_DIR" ]]; then
        log_message "⚠️  R analysis directory not found: $R_ANALYSIS_DIR"
        log_message "⚠️  Skipping R analysis, using existing statistical results"
        return
    fi
    
    python3 manage.py run_r_analysis \
        --r-script-path "$R_ANALYSIS_DIR/retraction_democracy_analysis.R" \
        --working-dir "$R_ANALYSIS_DIR" \
        --output-dir "./r_analysis_output" \
        --update-db \
        2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_message "✅ R analysis completed successfully"
    else
        log_message "⚠️  R analysis failed, but continuing with existing data"
        log_message "⚠️  This is normal if R packages are missing or retractions_democracy repo is not available"
    fi
}

# Function to update visualizations
update_visualizations() {
    log_message "Updating visualization cache..."
    
    python3 manage.py import_democracy_data \
        --update-visualizations \
        2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_message "✅ Visualization cache updated"
    else
        log_message "❌ Visualization update failed"
        exit 1
    fi
}

# Function to run Django checks
run_django_checks() {
    log_message "Running Django system checks..."
    
    python3 manage.py check 2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_message "✅ Django checks passed"
    else
        log_message "❌ Django checks failed"
        exit 1
    fi
}

# Function to collect static files (for production)
collect_static() {
    if [[ "$1" == "--production" ]]; then
        log_message "Collecting static files for production..."
        
        python3 manage.py collectstatic --noinput 2>&1 | tee -a "$LOG_FILE"
        
        if [[ $? -eq 0 ]]; then
            log_message "✅ Static files collected"
        else
            log_message "❌ Static file collection failed"
            exit 1
        fi
    fi
}

# Function to restart Django service (for production)
restart_django_service() {
    if [[ "$1" == "--production" ]]; then
        log_message "Restarting Django service..."
        
        # Modify this based on your server setup
        # Examples:
        # sudo systemctl restart gunicorn
        # sudo supervisorctl restart django
        # touch /path/to/wsgi.py  # for passenger/mod_wsgi
        
        # For development server, we'll just print a message
        log_message "🔄 In production, you would restart your Django service here"
        log_message "   Examples:"
        log_message "   - sudo systemctl restart gunicorn"
        log_message "   - sudo supervisorctl restart django"
        log_message "   - touch wsgi.py (for passenger)"
    fi
}

# Main execution function
main() {
    local production_mode=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                production_mode="--production"
                shift
                ;;
            --help)
                echo "Usage: $0 [--production] [--help]"
                echo ""
                echo "Options:"
                echo "  --production    Run in production mode (collect static, restart services)"
                echo "  --help         Show this help message"
                echo ""
                echo "This script runs the complete democracy analysis pipeline:"
                echo "1. Check prerequisites"
                echo "2. Import democracy data from R analysis"
                echo "3. Run R statistical analysis (optional)"
                echo "4. Update visualization cache"
                echo "5. Run Django system checks"
                echo "6. Collect static files (production only)"
                echo "7. Restart Django service (production only)"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    log_message "Starting democracy analysis pipeline..."
    log_message "Production mode: ${production_mode:-disabled}"
    log_message "Log file: $LOG_FILE"
    
    # Run the pipeline
    check_prerequisites
    run_django_import
    run_r_analysis  # This might fail, but we continue
    update_visualizations
    run_django_checks
    collect_static "$production_mode"
    restart_django_service "$production_mode"
    
    log_message "🎉 Democracy analysis pipeline completed successfully!"
    log_message "📊 Your democracy analysis is now available at: /democracy-analysis/"
    log_message "📋 Full log saved to: $LOG_FILE"
    
    # Show summary
    echo ""
    echo "📈 Analysis Summary:"
    echo "==================="
    
    # Get basic stats from Django
    python3 manage.py shell << 'EOF'
from papers.models import DemocracyData, DemocracyAnalysisResults
democracy_count = DemocracyData.objects.count()
results_count = DemocracyAnalysisResults.objects.count()
countries = DemocracyData.objects.values('country').distinct().count()
years = DemocracyData.objects.aggregate(
    min_year=models.Min('year'), 
    max_year=models.Max('year')
)
print(f"• {democracy_count:,} democracy data observations")
print(f"• {countries} unique countries")
print(f"• {years['min_year']}-{years['max_year']} time period")
print(f"• {results_count} statistical analysis results")
print("")
print("🌐 Website sections updated:")
print("• Democracy analysis page")
print("• Interactive visualizations")
print("• Statistical results tables")
print("• Methodology documentation")
EOF
}

# Run the main function
main "$@"