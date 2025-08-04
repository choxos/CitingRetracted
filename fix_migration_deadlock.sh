#!/bin/bash
# Fix Django Migration Deadlock Script
# Resolves the circular dependency between 0008 and 0009 migrations

echo "🔧 PRCT Migration Deadlock Fix"
echo "==============================="

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
echo "🔧 Step 1: Remove problematic 0009 migration temporarily..."
echo "=========================================================="

# Backup the 0009 migration
cp papers/migrations/0009_rename_ci_to_cri.py papers/migrations/0009_rename_ci_to_cri.py.backup
echo "✅ Backed up 0009 migration"

# Remove the 0009 migration temporarily
rm papers/migrations/0009_rename_ci_to_cri.py
echo "✅ Temporarily removed 0009 migration"

echo ""
echo "🔧 Step 2: Apply 0008 migration to create democracy tables..."
echo "============================================================"

# Now apply 0008 migration which should work
echo "🔄 Applying 0008 migration (create democracy tables)..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers

if [ $? -eq 0 ]; then
    echo "✅ 0008 migration applied successfully! Democracy tables created."
else
    echo "❌ 0008 migration failed. Restoring 0009 migration..."
    mv papers/migrations/0009_rename_ci_to_cri.py.backup papers/migrations/0009_rename_ci_to_cri.py
    exit 1
fi

echo ""
echo "🔧 Step 3: Restore and apply 0009 migration..."
echo "=============================================="

# Restore the 0009 migration
mv papers/migrations/0009_rename_ci_to_cri.py.backup papers/migrations/0009_rename_ci_to_cri.py
echo "✅ Restored 0009 migration"

# Now apply 0009 migration
echo "🔄 Applying 0009 migration (rename CI to CrI columns)..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py migrate papers

if [ $? -eq 0 ]; then
    echo "✅ 0009 migration applied successfully! Columns renamed to CrI."
else
    echo "❌ 0009 migration failed. Check error above."
    exit 1
fi

echo ""
echo "🔄 Step 4: Import democracy data..."
echo "==================================="

# Import the democracy data
echo "📊 Importing democracy analysis data..."
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py import_democracy_data

if [ $? -eq 0 ]; then
    echo "✅ Democracy data imported successfully!"
else
    echo "❌ Data import failed. Check error above."
    exit 1
fi

echo ""
echo "🔄 Step 5: Restart web server..."
echo "================================="

# Restart web server
echo "🔄 Restarting web server..."
sudo systemctl restart xeradb-prct.service

echo ""
echo "🎉 MIGRATION DEADLOCK RESOLVED!"
echo "==============================="
echo ""
echo "📋 Summary of what was completed:"
echo "  ✅ Temporarily removed conflicting 0009 migration"
echo "  ✅ Applied 0008 migration (created democracy tables)"
echo "  ✅ Restored and applied 0009 migration (renamed CI→CrI)"
echo "  ✅ Imported democracy analysis data"
echo "  ✅ Restarted web server"
echo ""
echo "🌐 Test the democracy analysis page:"
echo "   https://prct.xeradb.com/democracy-analysis/"
echo ""
echo "🎯 The 500 error should now be completely resolved!"