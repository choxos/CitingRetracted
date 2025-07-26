#!/bin/bash

# ============================================================================
# PRCT Port Configuration Setup Script
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 PRCT Port Configuration Setup${NC}"
echo "========================================="

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -n -e "${YELLOW}${prompt} [${default}]: ${NC}"
    read input
    if [ -z "$input" ]; then
        declare -g "$var_name"="$default"
    else
        declare -g "$var_name"="$input"
    fi
}

# Get current port from .env if it exists
CURRENT_PORT=""
if [ -f ".env" ]; then
    CURRENT_PORT=$(grep "^PRCT_PORT=" .env 2>/dev/null | cut -d'=' -f2 || echo "")
fi

# Set default port
DEFAULT_PORT=${CURRENT_PORT:-8001}

echo -e "${GREEN}📋 Current Configuration:${NC}"
if [ -f ".env" ]; then
    echo "   Found existing .env file"
    if [ ! -z "$CURRENT_PORT" ]; then
        echo "   Current port: $CURRENT_PORT"
    fi
else
    echo "   No .env file found - will create new one"
fi

echo ""
echo -e "${YELLOW}🔧 Configuration Options:${NC}"

# Prompt for configuration
prompt_with_default "Enter PRCT port" "$DEFAULT_PORT" "PRCT_PORT"
prompt_with_default "Enter PRCT host" "127.0.0.1" "PRCT_HOST"
prompt_with_default "Enter number of Gunicorn workers" "3" "PRCT_WORKERS"
prompt_with_default "Enter your domain (e.g., prct.xeradb.com)" "91.99.161.136" "PRCT_DOMAIN"

echo ""
echo -e "${GREEN}📝 Configuration Summary:${NC}"
echo "   🔌 Port: $PRCT_PORT"
echo "   🌐 Host: $PRCT_HOST"
echo "   ⚙️ Workers: $PRCT_WORKERS"
echo "   🌍 Domain: $PRCT_DOMAIN"

echo ""
read -p "Continue with this configuration? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Configuration cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔄 Updating configuration files...${NC}"

# Check if port is available
echo "   🔍 Checking if port $PRCT_PORT is available..."
if lsof -i :$PRCT_PORT >/dev/null 2>&1; then
    echo -e "${YELLOW}   ⚠️ Warning: Port $PRCT_PORT is currently in use${NC}"
    echo "   Run 'sudo lsof -i :$PRCT_PORT' to see what's using it"
    read -p "   Continue anyway? (y/N): " port_confirm
    if [[ ! $port_confirm =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Setup cancelled${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}   ✅ Port $PRCT_PORT is available${NC}"
fi

# Create or update .env file
echo "   📄 Updating .env file..."

# Backup existing .env if it exists
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "   💾 Backed up existing .env file"
fi

# Create .env from template if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "   📋 Created .env from env.example"
    else
        echo -e "${RED}   ❌ env.example not found!${NC}"
        exit 1
    fi
fi

# Update port configuration in .env
sed -i.bak \
    -e "s/^PRCT_PORT=.*/PRCT_PORT=$PRCT_PORT/" \
    -e "s/^PRCT_HOST=.*/PRCT_HOST=$PRCT_HOST/" \
    -e "s/^PRCT_WORKERS=.*/PRCT_WORKERS=$PRCT_WORKERS/" \
    -e "s/^PRCT_DOMAIN=.*/PRCT_DOMAIN=$PRCT_DOMAIN/" \
    .env

echo -e "${GREEN}   ✅ .env file updated${NC}"

# Update service configurations
echo "   ⚙️ Updating service configurations..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}   ❌ manage.py not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

# Run Django command to update configurations
python manage.py configure_services --all --dry-run
echo ""
read -p "Apply these service configuration changes? (y/N): " service_confirm
if [[ $service_confirm =~ ^[Yy]$ ]]; then
    python manage.py configure_services --all
    echo -e "${GREEN}   ✅ Service configurations updated${NC}"
else
    echo -e "${YELLOW}   ⚠️ Service configurations not applied${NC}"
    echo "   Run manually: python manage.py configure_services --all"
fi

echo ""
echo -e "${GREEN}🎉 Port configuration setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. 🔄 Restart services:"
echo "   ${BLUE}python manage.py manage_server restart${NC}"
echo ""
echo "2. 🧪 Test the configuration:"
echo "   ${BLUE}python manage.py manage_server test${NC}"
echo ""
echo "3. 🌐 Access your site:"
echo "   ${BLUE}http://$PRCT_HOST:$PRCT_PORT${NC}"
if [ "$PRCT_HOST" = "127.0.0.1" ]; then
    echo "   ${BLUE}http://$PRCT_DOMAIN/${NC} (external)"
fi
echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo "   ${BLUE}python manage.py manage_server status${NC}     - Check server status"
echo "   ${BLUE}python manage.py manage_server logs${NC}       - View logs"
echo "   ${BLUE}python manage.py manage_server --dev start${NC} - Start dev server"
echo ""
echo -e "${GREEN}🚀 Your PRCT is now configured for port $PRCT_PORT!${NC}" 