# 🔌 PRCT Port Configuration Guide

## 📋 Overview

Finally! No more remembering ports across different configuration files. PRCT now uses a centralized port configuration system through the `.env` file that automatically updates all services.

## 🎯 Benefits

✅ **Single Source of Truth**: All port configuration in `.env`  
✅ **Automatic Updates**: Services update automatically  
✅ **No More Conflicts**: Easy port switching  
✅ **Error Prevention**: No more mismatched configurations  
✅ **Easy Deployment**: One command setup  

## 🔧 Quick Setup

### **Option 1: Automated Setup (Recommended)**

```bash
# Run the setup script
chmod +x setup_port_config.sh
./setup_port_config.sh
```

The script will:
- Detect current configuration
- Prompt for new port settings
- Update all configuration files
- Check port availability
- Generate service configurations

### **Option 2: Manual Configuration**

```bash
# 1. Copy environment template
cp env.example .env

# 2. Edit your port settings
nano .env
```

Update these key variables:
```env
PRCT_PORT=8001          # Your desired port
PRCT_HOST=127.0.0.1     # Usually localhost
PRCT_WORKERS=3          # Number of Gunicorn workers
PRCT_DOMAIN=your-domain.com  # Your actual domain
```

```bash
# 3. Update service configurations
python manage.py configure_services --all

# 4. Restart services
python manage.py manage_server restart
```

## 📋 Environment Variables

### **Core Port Configuration**
```env
# Port Configuration - The heart of the system
PRCT_PORT=8001                    # Main application port
PRCT_HOST=127.0.0.1              # Bind address
PRCT_WORKERS=3                   # Gunicorn workers

# Domain Configuration
PRCT_DOMAIN=prct.xeradb.com      # Your domain name
```

### **Performance Settings**
```env
# Database & Cache
DB_CONN_MAX_AGE=600              # Database connection timeout
REDIS_URL=redis://127.0.0.1:6379 # Redis cache URL
CACHE_TTL=300                    # Default cache timeout

# Application Performance
ANALYTICS_CACHE_TIMEOUT=3600     # Analytics cache (1 hour)
ANALYTICS_BATCH_SIZE=1000        # Batch processing size
```

## 🛠️ Management Commands

### **🚀 Server Management**

```bash
# Start server (production)
python manage.py manage_server start

# Start development server
python manage.py manage_server start --dev

# Stop server
python manage.py manage_server stop

# Restart server
python manage.py manage_server restart

# Check status
python manage.py manage_server status

# View logs
python manage.py manage_server logs

# Follow logs in real-time
python manage.py manage_server logs --follow

# Test all endpoints
python manage.py manage_server test
```

### **⚙️ Service Configuration**

```bash
# Update all service configurations
python manage.py configure_services --all

# Update only Nginx
python manage.py configure_services --nginx

# Update only systemd
python manage.py configure_services --systemd

# Preview changes without applying
python manage.py configure_services --all --dry-run
```

## 🔄 Changing Ports

### **Quick Port Change**

```bash
# 1. Update .env file
sed -i 's/^PRCT_PORT=.*/PRCT_PORT=8002/' .env

# 2. Update configurations
python manage.py configure_services --all

# 3. Restart services
python manage.py manage_server restart

# 4. Test new configuration
python manage.py manage_server test
```

### **Port Conflict Resolution**

```bash
# Check what's using a port
sudo lsof -i :8001

# Find available ports
for port in {8001..8010}; do
    if ! lsof -i :$port > /dev/null; then
        echo "Port $port is available"
    fi
done

# Kill processes on a port (if needed)
sudo lsof -ti:8001 | xargs sudo kill -9
```

## 📁 Generated Configurations

### **Gunicorn Configuration**
The system generates `gunicorn_config_dynamic.py`:
```python
# Auto-generated from .env
bind = "127.0.0.1:8001"    # From PRCT_HOST:PRCT_PORT
workers = 3                # From PRCT_WORKERS
# ... other optimized settings
```

### **Nginx Configuration**
Auto-generates `/etc/nginx/sites-available/prct`:
```nginx
# Proxy to application
location / {
    proxy_pass http://127.0.0.1:8001;  # From .env
    # ... performance optimizations
}
```

### **Systemd Service**
Updates `/etc/systemd/system/prct-gunicorn.service`:
```ini
[Service]
EnvironmentFile=/var/www/prct/.env    # Reads all .env variables
ExecStart=.../gunicorn --config .../gunicorn_config_dynamic.py
```

## 🔍 Troubleshooting

### **Common Issues**

**1. Port Already in Use**
```bash
# Find what's using the port
sudo lsof -i :8001

# Kill the process
sudo kill -9 PID_NUMBER

# Or use the management command
python manage.py manage_server stop
```

**2. Configuration Not Applied**
```bash
# Regenerate all configurations
python manage.py configure_services --all

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart prct-gunicorn.service
```

**3. Permission Denied**
```bash
# The commands create temp files if no permission
# Copy them manually:
sudo cp /tmp/prct_config.* /etc/nginx/sites-available/prct
sudo systemctl daemon-reload
```

### **Debug Commands**

```bash
# Check current configuration
grep PRCT_PORT .env

# Test port connectivity
telnet 127.0.0.1 8001

# Check service status
python manage.py manage_server status

# View detailed logs
python manage.py manage_server logs --follow
```

## 🚀 Deployment Workflow

### **Development to Production**

```bash
# 1. Set production port in .env
echo "PRCT_PORT=8001" >> .env

# 2. Configure all services
python manage.py configure_services --all

# 3. Deploy and restart
git push origin main
ssh your-vps "cd /var/www/prct && git pull && python manage.py manage_server restart"
```

### **Multiple Environments**

```bash
# Development
cp env.example .env.dev
echo "PRCT_PORT=8000" >> .env.dev

# Staging  
cp env.example .env.staging
echo "PRCT_PORT=8001" >> .env.staging

# Production
cp env.example .env.production
echo "PRCT_PORT=8002" >> .env.production

# Switch environments
ln -sf .env.production .env
python manage.py configure_services --all
```

## 📊 Performance Impact

### **Before (Manual Configuration)**
- ❌ Port mismatches between services
- ❌ Manual updates across 4+ files
- ❌ Configuration drift
- ❌ Deployment errors

### **After (Centralized Configuration)**
- ✅ Single source of truth
- ✅ Automatic synchronization
- ✅ Error prevention
- ✅ Easy deployments

## 🎉 Success Examples

### **Quick Development Setup**
```bash
# Start development on port 8000
echo "PRCT_PORT=8000" > .env
python manage.py manage_server start --dev
# ✅ Runs on http://127.0.0.1:8000
```

### **Production Deployment**
```bash
# Deploy to VPS on port 8001
./setup_port_config.sh  # Interactive setup
python manage.py manage_server restart
# ✅ All services configured automatically
```

### **Port Migration**
```bash
# Move from 8001 to 8002
sed -i 's/PRCT_PORT=8001/PRCT_PORT=8002/' .env
python manage.py configure_services --all
python manage.py manage_server restart
# ✅ All services moved to new port
```

## 📚 Integration with Performance Features

The port configuration system works seamlessly with all performance optimizations:

- ✅ **Redis Caching**: Automatic cache configuration
- ✅ **Database Pooling**: Optimized connection settings
- ✅ **Static File Serving**: Nginx optimization
- ✅ **Load Balancing**: Multi-worker configuration
- ✅ **Monitoring**: Health checks on correct ports

## 🔗 Quick Reference

```bash
# Essential Commands
./setup_port_config.sh                    # Initial setup
python manage.py manage_server status     # Check everything
python manage.py manage_server restart    # Restart services
python manage.py configure_services --all # Update configs

# Environment Variables
PRCT_PORT=8001        # Main port
PRCT_HOST=127.0.0.1   # Bind address  
PRCT_WORKERS=3        # Worker count
PRCT_DOMAIN=your.com  # Domain name
```

## 🎯 Result

**No more port configuration headaches!** 🎉

Change one variable in `.env`, run one command, and everything updates automatically. Your port configuration is now:
- ✅ Centralized
- ✅ Automated  
- ✅ Error-free
- ✅ Easy to manage

**Finally, a sane way to manage ports in Django!** 🚀 