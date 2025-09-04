#!/bin/bash

# Fix VPS Migration Dependencies Script
# This script resolves migration dependency issues on the VPS where democracy analysis tables don't exist

echo "🔧 Fixing VPS Migration Dependencies..."
echo "========================================"

echo "📋 Step 1: Checking current migration status..."
python manage.py showmigrations papers

echo ""
echo "🎭 Step 2: Fake-applying democracy analysis migrations (tables don't exist on VPS)..."
echo "   Fake-applying 0008 (creates democracy tables)..."
python manage.py migrate papers 0008 --fake

echo "   Fake-applying 0009 (renames ci to cri columns)..."
python manage.py migrate papers 0009 --fake

echo "   Fake-applying 0010 (alters cri columns)..."
python manage.py migrate papers 0010 --fake

echo ""
echo "✅ Step 3: Running normal migration for any remaining migrations..."
python manage.py migrate

echo ""
echo "📋 Step 4: Final migration status check..."
python manage.py showmigrations papers

echo ""
echo "🎯 Migration fix complete!"
echo "   The democracy analysis migrations have been fake-applied since those tables"
echo "   don't exist on the VPS. All other migrations should now work normally."
echo ""
echo "🚀 You can now restart your Django service:"
echo "   sudo systemctl restart your-django-service"
