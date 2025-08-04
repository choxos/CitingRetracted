#!/bin/bash
# Apply the fixed migration script

echo "🔧 Applying Fixed Migration 0009"
echo "================================="

# Apply the migration with the correct dependency
echo "🔄 Applying migration 0009 (rename CI to CrI columns)..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers

if [ $? -eq 0 ]; then
    echo "✅ Migration 0009 applied successfully! Columns renamed to CrI."
    
    # Restart web server
    echo "🔄 Restarting web server..."
    sudo systemctl restart xeradb-prct.service
    
    echo ""
    echo "🎉 DEMOCRACY ANALYSIS FIXED!"
    echo "============================"
    echo ""
    echo "🌐 Test the democracy analysis page:"
    echo "   https://prct.xeradb.com/democracy-analysis/"
    echo ""
    echo "✅ The 500 error should now be resolved!"
else
    echo "❌ Migration failed. Check error above."
    exit 1
fi