import os
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Configure services (Nginx, systemd) based on .env port settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nginx',
            action='store_true',
            help='Update Nginx configuration'
        )
        parser.add_argument(
            '--systemd',
            action='store_true',
            help='Update systemd service configuration'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all service configurations'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )

    def handle(self, *args, **options):
        # Load environment variables
        load_dotenv()
        
        self.prct_port = os.getenv('PRCT_PORT', '8001')
        self.prct_host = os.getenv('PRCT_HOST', '127.0.0.1')
        self.domain = os.getenv('PRCT_DOMAIN', '91.99.161.136')
        self.ssl_enabled = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
        
        self.stdout.write(
            self.style.SUCCESS(f'🔧 Configuring services for {self.prct_host}:{self.prct_port}')
        )
        
        if options['all']:
            options['nginx'] = True
            options['systemd'] = True
        
        if options['nginx']:
            self.configure_nginx(options['dry_run'])
        
        if options['systemd']:
            self.configure_systemd(options['dry_run'])
        
        if not any([options['nginx'], options['systemd'], options['all']]):
            self.stdout.write(
                self.style.WARNING('No services specified. Use --nginx, --systemd, or --all')
            )
            self.show_current_config()

    def show_current_config(self):
        """Show current configuration from .env"""
        self.stdout.write(f'\n📋 Current Configuration:')
        self.stdout.write(f'   🌐 Host: {self.prct_host}')
        self.stdout.write(f'   🔌 Port: {self.prct_port}')
        self.stdout.write(f'   🌍 Domain: {self.domain}')
        self.stdout.write(f'   🔒 SSL: {"Enabled" if self.ssl_enabled else "Disabled"}')

    def configure_nginx(self, dry_run=False):
        """Generate Nginx configuration"""
        self.stdout.write('🌐 Configuring Nginx...')
        
        nginx_config = f"""server {{
    listen 80;
    server_name {self.domain} prct.xeradb.com www.prct.xeradb.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Static files (XeraDB theme) with compression
    location /static/ {{
        alias /var/www/prct/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compression
        gzip on;
        gzip_vary on;
        gzip_types text/css application/javascript application/json image/svg+xml;
        
        # Brotli compression (if available)
        brotli on;
        brotli_types text/css application/javascript application/json;
    }}
    
    # Media files
    location /media/ {{
        alias /var/www/prct/media/;
        expires 7d;
        add_header Cache-Control "public";
    }}
    
    # API endpoints with caching
    location /api/ {{
        proxy_pass http://{self.prct_host}:{self.prct_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # API response caching
        proxy_cache_valid 200 5m;
        proxy_cache_key "$scheme$request_method$host$request_uri";
    }}
    
    # Main application
    location / {{
        proxy_pass http://{self.prct_host}:{self.prct_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 60s;  # Longer for analytics
        
        # Enable compression
        gzip on;
        gzip_vary on;
        gzip_proxied any;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    }}
    
    # Security
    location ~ /\.ht {{
        deny all;
    }}
    
    # Favicon optimization
    location = /favicon.ico {{
        alias /var/www/prct/static/images/favicon.ico;
        log_not_found off;
        access_log off;
        expires 1y;
    }}
    
    # Robots.txt
    location = /robots.txt {{
        alias /var/www/prct/static/robots.txt;
        log_not_found off;
        access_log off;
    }}
}}"""

        if self.ssl_enabled:
            nginx_config += f"""

# SSL Configuration (redirect to HTTPS)
server {{
    listen 443 ssl http2;
    server_name {self.domain} prct.xeradb.com www.prct.xeradb.com;
    
    # SSL certificates (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/prct.xeradb.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/prct.xeradb.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Include the same location blocks from above
    # (Static files, media files, API, main application, etc.)
    # ... [Same configuration as HTTP version] ...
}}"""

        if dry_run:
            self.stdout.write('   📄 Nginx configuration preview:')
            self.stdout.write('   ' + '\n   '.join(nginx_config.split('\n')[:10]) + '\n   ...')
        else:
            config_path = '/etc/nginx/sites-available/prct'
            try:
                with open(config_path, 'w') as f:
                    f.write(nginx_config)
                self.stdout.write(self.style.SUCCESS(f'   ✅ Nginx config written to {config_path}'))
                self.stdout.write('   🔄 Run: sudo nginx -t && sudo systemctl reload nginx')
            except PermissionError:
                # Write to temp file for manual copying
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nginx') as f:
                    f.write(nginx_config)
                    temp_path = f.name
                
                self.stdout.write(self.style.WARNING(f'   ⚠️ Permission denied. Config saved to: {temp_path}'))
                self.stdout.write(f'   📋 Copy with: sudo cp {temp_path} /etc/nginx/sites-available/prct')

    def configure_systemd(self, dry_run=False):
        """Generate systemd service configuration"""
        self.stdout.write('⚙️ Configuring systemd service...')
        
        systemd_config = f"""[Unit]
Description=PRCT Gunicorn daemon
Requires=prct-gunicorn.socket
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=xeradb
Group=xeradb
RuntimeDirectory=prct
WorkingDirectory=/var/www/prct
EnvironmentFile=/var/www/prct/.env
ExecStart=/var/www/prct/venv/bin/gunicorn \\
    --config /var/www/prct/gunicorn_config_dynamic.py \\
    citing_retracted.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target"""

        socket_config = f"""[Unit]
Description=PRCT Gunicorn socket

[Socket]
ListenStream=/run/prct.sock
ListenStream={self.prct_host}:{self.prct_port}
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target"""

        if dry_run:
            self.stdout.write('   📄 Systemd service configuration preview:')
            self.stdout.write('   ' + '\n   '.join(systemd_config.split('\n')[:10]) + '\n   ...')
        else:
            service_path = '/etc/systemd/system/prct-gunicorn.service'
            socket_path = '/etc/systemd/system/prct-gunicorn.socket'
            
            try:
                with open(service_path, 'w') as f:
                    f.write(systemd_config)
                with open(socket_path, 'w') as f:
                    f.write(socket_config)
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Systemd configs written'))
                self.stdout.write('   🔄 Run: sudo systemctl daemon-reload && sudo systemctl restart prct-gunicorn.service')
            except PermissionError:
                # Write to temp files
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as f:
                    f.write(systemd_config)
                    service_temp = f.name
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.socket') as f:
                    f.write(socket_config)
                    socket_temp = f.name
                
                self.stdout.write(self.style.WARNING(f'   ⚠️ Permission denied. Configs saved to temp files:'))
                self.stdout.write(f'   📋 Service: sudo cp {service_temp} {service_path}')
                self.stdout.write(f'   📋 Socket: sudo cp {socket_temp} {socket_path}') 