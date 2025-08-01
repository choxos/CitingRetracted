# SSL Setup Guide for PRCT on Hetzner

This guide covers setting up SSL certificates for your PRCT application using Let's Encrypt.

## Prerequisites

- Domain `prct.xeradb.com` should be pointing to your server's IP address
- Nginx installed and HTTP configuration working
- Port 80 and 443 open in your firewall

## Step 1: Install Certbot

```bash
# Install certbot and nginx plugin
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Verify installation
certbot --version
```

## Step 2: Stop Nginx Temporarily (if needed)

```bash
sudo systemctl stop nginx
```

## Step 3: Obtain SSL Certificate

### Option A: Using nginx plugin (recommended)
```bash
# Start nginx first if stopped
sudo systemctl start nginx

# Get certificate using nginx plugin
sudo certbot --nginx -d prct.xeradb.com

# Follow the prompts:
# - Enter email address
# - Agree to terms of service
# - Choose whether to share email with EFF
# - Select redirect option (recommended: redirect HTTP to HTTPS)
```

### Option B: Standalone method (if nginx plugin fails)
```bash
# Stop nginx
sudo systemctl stop nginx

# Get certificate using standalone method
sudo certbot certonly --standalone -d prct.xeradb.com

# Start nginx after getting certificate
sudo systemctl start nginx
```

## Step 4: Update Nginx Configuration

If you used Option B or need to manually configure, update your nginx config:

```bash
sudo nano /etc/nginx/sites-available/prct.xeradb.com
```

Use this SSL-enabled configuration:

```nginx
server {
    listen 80;
    server_name prct.xeradb.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name prct.xeradb.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/prct.xeradb.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/prct.xeradb.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net https://d3js.org; img-src 'self' data: blob: https:; connect-src 'self' https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files
    location /static/ {
        alias /var/www/prct/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/prct/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Step 5: Test and Reload Nginx

```bash
# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

## Step 6: Verify SSL Certificate

```bash
# Check certificate details
sudo certbot certificates

# Test SSL configuration
curl -I https://prct.xeradb.com

# Or use online SSL checker
# https://www.ssllabs.com/ssltest/analyze.html?d=prct.xeradb.com
```

## Step 7: Set Up Auto-Renewal

```bash
# Test auto-renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal (certbot usually does this automatically)
sudo crontab -e

# Add this line if not already present:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Troubleshooting

### Common Issues:

1. **Domain not pointing to server**
   ```bash
   # Check DNS resolution
   nslookup prct.xeradb.com
   dig prct.xeradb.com
   ```

2. **Firewall blocking ports**
   ```bash
   # Check firewall status
   sudo ufw status
   
   # Open required ports if needed
   sudo ufw allow 80
   sudo ufw allow 443
   ```

3. **Nginx not serving on port 80**
   ```bash
   # Check if nginx is listening on port 80
   sudo netstat -tlnp | grep :80
   
   # Check nginx status
   sudo systemctl status nginx
   ```

4. **Certificate validation failing**
   ```bash
   # Check if .well-known is accessible
   curl http://prct.xeradb.com/.well-known/acme-challenge/test
   ```

### Error Solutions:

- **"nginx: [emerg] cannot load certificate"**: Certificate files don't exist
  - Solution: Re-run certbot to generate certificates

- **"Connection refused"**: Nginx not running or wrong port
  - Solution: `sudo systemctl start nginx`

- **"DNS resolution failed"**: Domain not pointing to server
  - Solution: Update DNS A record to point to your server IP

## Security Best Practices

1. **Update Django settings for HTTPS**:
   ```python
   # In settings/production.py
   SECURE_SSL_REDIRECT = True
   SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

2. **Regular certificate monitoring**:
   ```bash
   # Check certificate expiry
   echo | openssl s_client -connect prct.xeradb.com:443 2>/dev/null | openssl x509 -noout -dates
   ```

3. **Backup certificates** (optional but recommended):
   ```bash
   sudo cp -r /etc/letsencrypt /backup/letsencrypt-$(date +%Y%m%d)
   ```

## Next Steps

After SSL is working:
1. Update any hardcoded HTTP URLs to HTTPS
2. Test all functionality with HTTPS
3. Monitor certificate renewal
4. Consider setting up monitoring alerts for certificate expiry 