#!/bin/bash

# PRCT XeraDB Theme Deployment Script
# Run this script to deploy the migrated XeraDB theme to production

echo "🎨 Starting PRCT XeraDB Theme Deployment..."
echo "================================================"

# Step 1: Merge migration branch to main
echo "📁 Merging migration branch to main..."
git checkout main
git merge xeradb-theme-migration --no-ff -m "Deploy: Complete PRCT XeraDB theme migration"

# Step 2: Collect static files
echo "📦 Collecting static files..."
python3 manage.py collectstatic --noinput

# Step 3: Check Django configuration
echo "🔍 Checking Django configuration..."
python3 manage.py check --deploy

# Step 4: Push to remote repository
echo "🚀 Pushing to remote repository..."
git push origin main

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================"
echo "🎉 PRCT XeraDB theme is now deployed!"
echo ""
echo "📋 Next steps for VPS deployment:"
echo "1. SSH to your VPS"
echo "2. cd /path/to/CitingRetracted"
echo "3. git pull origin main"
echo "4. python3 manage.py collectstatic --noinput"
echo "5. sudo systemctl restart gunicorn"
echo "6. sudo systemctl restart nginx"
echo ""
echo "🔗 Visit your site to see the new XeraDB theme!"
echo "📊 All 12+ charts and visualizations preserved!"
echo "🎨 Modern, professional PRCT interface ready!" 