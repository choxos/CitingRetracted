import os
import subprocess
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Manage PRCT server with automatic port configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'restart', 'status', 'logs', 'test'],
            help='Action to perform'
        )
        parser.add_argument(
            '--dev',
            action='store_true',
            help='Run in development mode (Django dev server)'
        )
        parser.add_argument(
            '--follow',
            action='store_true',
            help='Follow logs (with logs action)'
        )

    def handle(self, *args, **options):
        # Load environment variables
        load_dotenv()
        
        self.prct_port = os.getenv('PRCT_PORT', '8001')
        self.prct_host = os.getenv('PRCT_HOST', '127.0.0.1')
        
        action = options['action']
        dev_mode = options['dev']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 PRCT Server Management - {self.prct_host}:{self.prct_port}')
        )
        
        if action == 'start':
            self.start_server(dev_mode)
        elif action == 'stop':
            self.stop_server(dev_mode)
        elif action == 'restart':
            self.restart_server(dev_mode)
        elif action == 'status':
            self.show_status()
        elif action == 'logs':
            self.show_logs(options['follow'])
        elif action == 'test':
            self.test_server()

    def start_server(self, dev_mode=False):
        """Start the server"""
        self.stdout.write('🚀 Starting server...')
        
        if dev_mode:
            self.stdout.write(f'   📍 Development server: http://{self.prct_host}:{self.prct_port}')
            cmd = [
                'python', 'manage.py', 'runserver', 
                f'{self.prct_host}:{self.prct_port}',
                '--settings=citing_retracted.settings_production'
            ]
            try:
                subprocess.run(cmd, check=True)
            except KeyboardInterrupt:
                self.stdout.write('\n   🛑 Development server stopped')
        else:
            # Production mode
            self.stdout.write('   🔧 Starting production services...')
            
            # Start Gunicorn service
            result = subprocess.run(['sudo', 'systemctl', 'start', 'prct-gunicorn.service'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('   ✅ Gunicorn service started'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to start Gunicorn: {result.stderr}'))
            
            # Start Nginx
            result = subprocess.run(['sudo', 'systemctl', 'start', 'nginx'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('   ✅ Nginx started'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to start Nginx: {result.stderr}'))
            
            # Test the setup
            time.sleep(2)
            self.test_server()

    def stop_server(self, dev_mode=False):
        """Stop the server"""
        self.stdout.write('🛑 Stopping server...')
        
        if dev_mode:
            # Kill development server processes
            subprocess.run(['pkill', '-f', 'manage.py.*runserver'], 
                         capture_output=True)
            self.stdout.write('   ✅ Development server stopped')
        else:
            # Stop production services
            subprocess.run(['sudo', 'systemctl', 'stop', 'prct-gunicorn.service'])
            self.stdout.write('   ✅ Gunicorn service stopped')

    def restart_server(self, dev_mode=False):
        """Restart the server"""
        self.stdout.write('🔄 Restarting server...')
        
        if dev_mode:
            self.stop_server(dev_mode)
            time.sleep(1)
            self.start_server(dev_mode)
        else:
            # Restart production services
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'prct-gunicorn.service'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('   ✅ Gunicorn service restarted'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to restart: {result.stderr}'))
            
            subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'])
            self.stdout.write('   ✅ Nginx reloaded')
            
            time.sleep(2)
            self.test_server()

    def show_status(self):
        """Show server status"""
        self.stdout.write('📊 Server Status:')
        
        # Check if port is in use
        result = subprocess.run(['lsof', '-i', f':{self.prct_port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Port {self.prct_port} is active'))
            # Show what's using the port
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    self.stdout.write(f'      🔹 {parts[0]} (PID: {parts[1]})')
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Port {self.prct_port} not in use'))
        
        # Check systemd services
        services = ['prct-gunicorn.service', 'nginx', 'redis', 'postgresql']
        for service in services:
            result = subprocess.run(['systemctl', 'is-active', service], 
                                  capture_output=True, text=True)
            status = result.stdout.strip()
            if status == 'active':
                self.stdout.write(self.style.SUCCESS(f'   ✅ {service}: {status}'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ {service}: {status}'))

    def show_logs(self, follow=False):
        """Show server logs"""
        self.stdout.write('📋 Server Logs:')
        
        log_files = [
            '/var/log/prct/gunicorn_error.log',
            '/var/log/prct/gunicorn_access.log',
            '/var/log/prct/django.log'
        ]
        
        if follow:
            self.stdout.write('   📡 Following logs (Ctrl+C to stop)...')
            try:
                # Follow Gunicorn error log
                subprocess.run(['tail', '-f'] + log_files, check=True)
            except KeyboardInterrupt:
                self.stdout.write('\n   🛑 Log following stopped')
        else:
            for log_file in log_files:
                if os.path.exists(log_file):
                    self.stdout.write(f'\n   📄 {log_file} (last 10 lines):')
                    try:
                        result = subprocess.run(['tail', '-n', '10', log_file], 
                                              capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.stdout.write(f'      {line}')
                    except Exception as e:
                        self.stdout.write(f'      ❌ Error reading log: {e}')

    def test_server(self):
        """Test server connectivity"""
        self.stdout.write('🧪 Testing server...')
        
        import requests
        
        base_url = f'http://{self.prct_host}:{self.prct_port}'
        
        # Test endpoints
        endpoints = [
            ('/', 'Homepage'),
            ('/analytics/', 'Analytics'),
            ('/search/', 'Search')
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(base_url + endpoint, timeout=10)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ {name}: OK ({response.status_code})'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ {name}: {response.status_code}'))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'   ❌ {name}: Connection failed ({e})'))
        
        self.stdout.write(f'\n   🌐 Access your site: http://{self.prct_host}:{self.prct_port}')
        
        # Show helpful URLs
        if self.prct_host == '127.0.0.1':
            domain = os.getenv('PRCT_DOMAIN', '91.99.161.136')
            self.stdout.write(f'   🌍 External access: http://{domain}/')
            self.stdout.write(f'   📊 Analytics: http://{domain}/analytics/')
            self.stdout.write(f'   🔍 Search: http://{domain}/search/') 