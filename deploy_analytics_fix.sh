#!/bin/bash

# Analytics Charts Fix Deployment Script
# Run this on your VPS to fix all analytics chart issues

set -e  # Exit on any error

echo "🔧 Deploying Analytics Charts Fix..."

# Update nginx configuration with proper CSP headers
echo "📝 Updating nginx configuration..."
sudo cp nginx_csp_update.txt /etc/nginx/sites-available/prct.xeradb.com

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Reload nginx if test passes
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Collect static files to ensure service worker is deployed
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Restart Django application
echo "🚀 Restarting Django application..."
sudo systemctl restart prct

# Verify CSP header
echo "✅ Verifying CSP header..."
echo "CSP Header:"
curl -s -I https://prct.xeradb.com | grep -i content-security-policy || echo "❌ CSP header not found"

echo ""
echo "🎉 Analytics Fix Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Clear your browser cache (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Visit https://prct.xeradb.com/analytics/"
echo "3. Check that all chart tabs now work properly"
echo ""
echo "If charts still don't work:"
echo "- Try an incognito/private browser window"
echo "- Check browser console for any remaining errors"
echo "- Verify the CSP header above includes all necessary domains" 