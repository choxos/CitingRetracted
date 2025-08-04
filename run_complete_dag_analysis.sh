#!/bin/bash

# Complete DAG-based Democracy Analysis Script
# This script runs the full Bayesian hierarchical model with ALL confounding variables

set -e  # Exit on any error

echo "🔬 Starting Complete DAG-based Democracy Analysis"
echo "================================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set Django settings for production
export DJANGO_SETTINGS_MODULE=citing_retracted.production_settings

echo "📊 Step 1: Import democracy data into Django models..."
python3 manage.py import_democracy_data --clear-existing --update-visualizations

echo ""
echo "🧮 Step 2: Run complete R analysis with ALL confounding variables..."
echo "Variables included in DAG-based model:"
echo "  ✅ Democracy Index (main predictor)"
echo "  ✅ English Proficiency"
echo "  ✅ GDP per Capita"
echo "  ✅ Control of Corruption"
echo "  ✅ Government Effectiveness"
echo "  ✅ Regulatory Quality"
echo "  ✅ Rule of Law"
echo "  ✅ International Collaboration"
echo "  ✅ Power Distance Index (PDI)"
echo "  ✅ R&D Spending (% GDP)"
echo "  ✅ Press Freedom Index"

python3 manage.py run_r_analysis --update-db \
    --working-dir "../retractions_democracy/" \
    --output-dir "./r_analysis_output/"

echo ""
echo "🌐 Step 3: Update static files..."
python3 manage.py collectstatic --noinput

echo ""
echo "🔄 Step 4: Restart web server..."
if command -v systemctl &> /dev/null; then
    echo "Restarting systemd service..."
    sudo systemctl restart xeradb-prct.service
    echo "Service restarted successfully"
elif pgrep gunicorn > /dev/null; then
    echo "Restarting Gunicorn manually..."
    pkill -HUP gunicorn
    echo "Gunicorn restarted successfully"
else
    echo "⚠️  Please restart your web server manually"
fi

echo ""
echo "✅ Complete DAG-based analysis deployment finished!"
echo ""
echo "🎯 What was implemented:"
echo "  • Full Bayesian hierarchical Poisson Inverse Gaussian (PIG) models"
echo "  • Multiple imputation (MICE) for missing data handling"
echo "  • Year-specific scaling of all variables"
echo "  • Both univariate and full multivariate models"
echo "  • All 11 confounding variables from the DAG"
echo "  • 95% Credible Intervals (CrI) for Bayesian inference"
echo ""
echo "🌐 View results at: https://prct.xeradb.com/democracy-analysis/"
echo "📊 The regression table now shows complete results for all variables"
echo "🔍 Raw Data Explorer includes all model variables with statistics"
echo "📈 Model Diagnostics shows comprehensive Bayesian diagnostics"