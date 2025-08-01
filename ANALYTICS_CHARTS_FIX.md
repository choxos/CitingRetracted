# Analytics Charts Fix Documentation

## Issue Summary

The analytics charts on https://prct.xeradb.com were not displaying properly due to several Content Security Policy (CSP) violations and configuration issues.

## Problems Identified

### 1. Content Security Policy (CSP) Violations
- Google Fonts blocked from `fonts.googleapis.com`
- Font Awesome blocked from `cdnjs.cloudflare.com`
- D3.js blocked from `d3js.org`
- Plotly.js required `'unsafe-eval'` permissions

### 2. Browser Console Errors
```
Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"

Refused to load the script 'https://d3js.org/d3.v7.min.js' because it violates the following Content Security Policy directive: "script-src 'self' 'unsafe-inline' https://cdn.plot.ly https://cdn.jsdelivr.net"

Uncaught EvalError: Refused to evaluate a string as JavaScript because 'unsafe-eval' is not an allowed source of script in the following Content Security Policy directive: "script-src 'self' 'unsafe-inline' https://cdn.plot.ly https://cdn.jsdelivr.net"

Uncaught ReferenceError: d3 is not defined
```

### 3. Missing Service Worker
- 404 error for `/sw.js` preventing service worker registration

### 4. Outdated Plotly.js Version
- Using deprecated `plotly-latest.min.js` (v1.58.5 from July 2021)

### 5. Duplicate Script Loading
- `performance-optimizations.js` loaded twice causing identifier conflicts

## Fixes Applied

### 1. Updated Nginx CSP Configuration
**File:** `SSL_SETUP_GUIDE.md`

**Old CSP:**
```nginx
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

**New CSP:**
```nginx
add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net https://d3js.org; img-src 'self' data: blob: https:; connect-src 'self' https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none';" always;
```

**Changes:**
- Added explicit domains for style sources
- Added font sources for Google Fonts and Font Awesome
- Added `'unsafe-eval'` for Plotly.js functionality
- Added `d3js.org` to script sources
- Improved security with specific directives

### 2. Created Service Worker
**File:** `static/sw.js`

Created a basic service worker for caching static assets:
```javascript
const CACHE_NAME = 'prct-analytics-v1';
const urlsToCache = ['/static/css/', '/static/js/', '/static/images/'];
```

### 3. Fixed Service Worker Registration
**File:** `templates/xera_base.html`

Updated path from `/sw.js` to `/static/sw.js`:
```javascript
navigator.serviceWorker.register('/static/sw.js')
```

### 4. Updated Plotly.js Version
**File:** `templates/papers/analytics.html`

Changed from deprecated version to current stable:
```html
<!-- Old -->
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<!-- New -->
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
```

### 5. Removed Duplicate Script Loading
**File:** `templates/xera_base.html`

Removed duplicate `performance-optimizations.js` inclusion to prevent identifier conflicts.

## Deployment Instructions

### 1. Update Nginx Configuration
```bash
# Edit the nginx configuration
sudo nano /etc/nginx/sites-available/prct.xeradb.com

# Update the CSP header as shown above

# Test the configuration
sudo nginx -t

# Reload nginx if test passes
sudo systemctl reload nginx
```

### 2. Deploy Updated Files
```bash
# Copy the service worker to static files
cp static/sw.js /var/www/prct/static/

# Collect static files
python manage.py collectstatic --noinput

# Restart the Django application
sudo systemctl restart prct
```

### 3. Clear Browser Cache
Instruct users to:
1. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache for the domain
3. Open Developer Tools and disable cache while DevTools is open

## Verification Steps

After deployment, verify the fixes by:

1. **Check Analytics Page**
   - Navigate to https://prct.xeradb.com/analytics/
   - Verify all chart tabs display content:
     - Trends
     - Citation Timing Distribution
     - Subject Hierarchy Sunburst
     - Geographic Distribution
     - Article Type Analysis
     - Publisher Analysis
     - Open Access Analysis

2. **Browser Console**
   - Open Developer Tools (F12)
   - Check for absence of CSP violations
   - Verify service worker registration success
   - Confirm D3.js and Plotly.js load properly

3. **Network Tab**
   - Verify all external resources load successfully (200 status)
   - Check that fonts load from Google Fonts
   - Confirm CDN resources are accessible

## Expected Results

After implementing these fixes:
- ✅ All analytics charts should display properly
- ✅ No CSP violation errors in console
- ✅ Service worker registers successfully
- ✅ Google Fonts and Font Awesome load correctly
- ✅ Interactive features (D3.js network charts, Plotly maps) work
- ✅ Modern Plotly.js version provides better performance

## Troubleshooting

If charts still don't appear:

1. **Check nginx logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Verify static files:**
   ```bash
   ls -la /var/www/prct/static/sw.js
   ```

3. **Test CSP header:**
   ```bash
   curl -I https://prct.xeradb.com | grep -i content-security-policy
   ```

4. **Django logs:**
   ```bash
   sudo journalctl -u prct -f
   ```

## Security Notes

The updated CSP maintains security while allowing necessary external resources:
- Only specific trusted domains are whitelisted
- `'unsafe-eval'` is limited to script sources where required by Plotly.js
- Frame ancestors are still blocked (`frame-ancestors 'none'`)
- Object sources are blocked (`object-src 'none'`)
- Base URI is restricted to same origin

This configuration balances functionality with security best practices. 