#!/bin/bash
# Demo runner script for Predatory Journal Detector
# This script sets up and runs the demonstration

set -e

echo "🎯 Predatory Journal Detector - Demo Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.9+ is installed
check_python() {
    print_status "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
        MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 9 ]; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.9+"
        return 1
    fi
}

# Check if Chrome is installed (for Selenium)
check_chrome() {
    print_status "Checking for Google Chrome..."
    if command -v google-chrome &> /dev/null; then
        print_success "Google Chrome found"
        return 0
    elif command -v chromium &> /dev/null; then
        print_success "Chromium found"
        return 0
    elif command -v chromium-browser &> /dev/null; then
        print_success "Chromium browser found"
        return 0
    else
        print_warning "Chrome/Chromium not found. Some features may not work."
        print_warning "Install Chrome: https://www.google.com/chrome/"
        return 0
    fi
}

# Setup virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from example"
            print_warning "Please edit .env file with your configuration"
        else
            print_warning "No .env.example found, using defaults"
        fi
    else
        print_status "Environment file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p models
    mkdir -p data
    mkdir -p cache
    
    print_success "Directories created"
}

# Download NLTK data
download_nltk_data() {
    print_status "Downloading NLTK data..."
    
    python3 -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
    print('✅ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠️  NLTK download failed: {e}')
"
}

# Run system checks
run_system_checks() {
    print_status "Running system checks..."
    
    python3 -c "
import sys
import importlib

# Check critical imports
critical_modules = [
    'requests', 'beautifulsoup4', 'selenium', 'pandas', 'numpy',
    'scikit-learn', 'xgboost', 'lightgbm', 'fastapi', 'uvicorn'
]

failed = []
for module in critical_modules:
    try:
        if module == 'beautifulsoup4':
            importlib.import_module('bs4')
        elif module == 'scikit-learn':
            importlib.import_module('sklearn')
        else:
            importlib.import_module(module.replace('-', '_'))
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module}')
        failed.append(module)

if failed:
    print(f'\\n⚠️  Failed to import: {failed}')
    sys.exit(1)
else:
    print('\\n✅ All critical modules imported successfully')
"
    
    if [ $? -eq 0 ]; then
        print_success "System checks passed"
    else
        print_error "System checks failed"
        return 1
    fi
}

# Run demo options
run_demo() {
    print_status "Starting demo..."
    echo ""
    echo "Demo Options:"
    echo "1. Quick demo (single journal analysis)"
    echo "2. Full demo (all features)"
    echo "3. API server demo"
    echo "4. Feature extraction demo"
    echo ""
    
    read -p "Choose demo option (1-4): " choice
    
    case $choice in
        1)
            print_status "Running quick demo..."
            python3 basic_demo.py
            ;;
        2)
            print_status "Running basic demo..."
            python3 basic_demo.py
            ;;
        3)
            print_status "Starting API server..."
            print_status "Visit http://localhost:8000/docs for interactive API documentation"
            python3 api/main.py
            ;;
        4)
            print_status "Running feature extraction demo..."
            python3 basic_demo.py
            ;;
        *)
            print_warning "Invalid choice, running basic demo..."
            python3 basic_demo.py
            ;;
    esac
}

# Main execution
main() {
    echo ""
    print_status "Starting Predatory Journal Detector demo setup..."
    echo ""
    
    # Run checks
    if ! check_python; then
        exit 1
    fi
    
    check_chrome
    
    # Setup environment
    setup_venv
    install_dependencies
    setup_environment
    create_directories
    download_nltk_data
    
    # Run system checks
    if ! run_system_checks; then
        print_error "Setup failed. Please check the errors above."
        exit 1
    fi
    
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    
    # Ask if user wants to run demo
    read -p "Run demo now? (y/n): " run_now
    
    if [[ $run_now =~ ^[Yy]$ ]]; then
        run_demo
    else
        echo ""
        print_status "Setup complete. You can run the demo later with:"
        echo "  source venv/bin/activate"
        echo "  python3 demo.py"
        echo ""
        print_status "Or start the API server with:"
        echo "  source venv/bin/activate"
        echo "  python3 api/main.py"
        echo ""
    fi
}

# Run main function
main "$@"
