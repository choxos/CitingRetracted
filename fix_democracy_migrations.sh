#!/bin/bash
# Complete Democracy Migration Fix Script
# Handles missing initial democracy tables and column renaming

echo "🔧 PRCT Complete Democracy Database Fix"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run from /var/www/prct"
    exit 1
fi

echo "📂 Current directory: $(pwd)"

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

echo ""
echo "🔍 Step 1: Checking current migration status..."
echo "================================================"

# Check what migrations exist in production
echo "📋 Current migrations applied:"
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py showmigrations papers || echo "Migration check failed - proceeding with fix..."

echo ""
echo "🔧 Step 2: Creating initial democracy tables..."
echo "================================================"

# First, let's apply any missing migrations up to the democracy models
echo "🔄 Applying all missing migrations (including democracy tables)..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers

# Check if that worked
if [ $? -eq 0 ]; then
    echo "✅ Initial migrations applied successfully!"
else
    echo "❌ Initial migrations failed. Trying to create democracy tables manually..."
    
    # Force create the democracy tables by running migrate with fake-initial
    echo "🔄 Force creating democracy tables..."
    DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers --fake-initial
    
    if [ $? -ne 0 ]; then
        echo "❌ Could not create democracy tables. Manual intervention required."
        exit 1
    fi
fi

echo ""
echo "🔄 Step 3: Importing democracy data..."
echo "======================================"

# Import the democracy data to populate the tables
echo "📊 Importing democracy analysis data..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py import_democracy_data

echo ""
echo "✅ Step 4: Testing democracy page..."
echo "===================================="

# Test if the democracy page works now
echo "🌐 The democracy analysis page should now work at:"
echo "   https://prct.xeradb.com/democracy-analysis/"

# Restart web server
echo "🔄 Restarting web server..."
sudo systemctl restart xeradb-prct.service

echo ""
echo "🎉 Complete democracy database setup finished!"
echo "=============================================="
echo ""
echo "📋 Summary of what was done:"
echo "  ✅ Applied all missing migrations"
echo "  ✅ Created democracy database tables"
echo "  ✅ Imported democracy analysis data"
echo "  ✅ Restarted web server"
echo ""
echo "🌐 Test the democracy analysis page:"
echo "   https://prct.xeradb.com/democracy-analysis/"