#!/bin/bash
# Database Column Fix Script for VPS Deployment
# Fixes the CI → CrI column naming issue

echo "🔧 PRCT Database Column Fix"
echo "============================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run from /var/www/prct"
    exit 1
fi

echo "📂 Current directory: $(pwd)"

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Check migration status
echo "📋 Checking migration status..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py showmigrations papers

# Apply the migration
echo "🔄 Applying database migration..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully!"
    
    # Restart web server
    echo "🔄 Restarting web server..."
    sudo systemctl restart xeradb-prct.service
    
    echo "🎉 Database fix complete!"
    echo "🌐 Test the democracy analysis page at:"
    echo "   https://prct.xeradb.com/democracy-analysis/"
else
    echo "❌ Migration failed! Check the error above."
    exit 1
fi