#!/bin/bash
# Production Database Diagnostic Script
# Checks what actually exists in the production database

echo "🔍 PRCT Production Database Diagnostic"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run from /var/www/prct"
    exit 1
fi

echo "📂 Current directory: $(pwd)"

echo ""
echo "🔍 Step 1: Check applied migrations in production..."
echo "==================================================="

# Check what migrations are actually recorded as applied
echo "📋 Migrations recorded as applied in production:"
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute('SELECT app, name FROM django_migrations WHERE app = %s ORDER BY applied;', ['papers'])
    migrations = cursor.fetchall()
    print('Applied migrations in papers app:')
    for app, name in migrations:
        print(f'  ✅ {app}.{name}')
    print(f'Total: {len(migrations)} migrations applied')
except Exception as e:
    print(f'❌ Error checking migrations: {e}')
"

echo ""
echo "🔍 Step 2: Check if democracy tables exist..."
echo "=============================================="

# Check if democracy tables exist in the database
echo "🗄️ Checking for democracy tables in production database:"
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    # Check for democracy tables
    cursor.execute(\"\"\"
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'papers_democracy%'
    ORDER BY table_name;
    \"\"\")
    tables = cursor.fetchall()
    print('Democracy tables found:')
    for (table_name,) in tables:
        print(f'  📊 {table_name}')
    print(f'Total democracy tables: {len(tables)}')
    
    if len(tables) == 0:
        print('❌ No democracy tables found in production database!')
    else:
        # Check structure of each table
        for (table_name,) in tables:
            cursor.execute(\"\"\"
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
            \"\"\", [table_name])
            columns = cursor.fetchall()
            print(f'\\n📋 {table_name} columns:')
            for col_name, data_type in columns:
                print(f'    - {col_name}: {data_type}')
                
except Exception as e:
    print(f'❌ Error checking tables: {e}')
"

echo ""
echo "🔍 Step 3: Check migration files on disk..."
echo "==========================================="

# List migration files
echo "📁 Migration files on disk:"
ls -la papers/migrations/00*.py | while read -r line; do
    echo "  $line"
done

echo ""
echo "🔍 Step 4: Check if models can be imported..."
echo "============================================"

# Try to import democracy models
echo "🔧 Testing democracy model imports:"
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 manage.py shell -c "
try:
    from papers.models import DemocracyData, DemocracyAnalysisResults, DemocracyVisualizationData
    print('✅ Democracy models import successfully')
    
    # Try to count records
    try:
        data_count = DemocracyData.objects.count()
        results_count = DemocracyAnalysisResults.objects.count()
        viz_count = DemocracyVisualizationData.objects.count()
        print(f'📊 Data counts:')
        print(f'  - DemocracyData: {data_count}')
        print(f'  - DemocracyAnalysisResults: {results_count}')
        print(f'  - DemocracyVisualizationData: {viz_count}')
    except Exception as e:
        print(f'❌ Error counting records: {e}')
        
except ImportError as e:
    print(f'❌ Cannot import democracy models: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "🎯 DIAGNOSTIC COMPLETE!"
echo "======================="
echo ""
echo "Based on the results above, we can determine:"
echo "  1. What migrations are actually applied in production"
echo "  2. Whether democracy tables exist or not"
echo "  3. What the next steps should be"