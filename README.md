# Post-Retraction Citation Tracker (PRCT)

A comprehensive database tracking retracted scientific papers and their post-retraction citations, helping researchers identify potential issues in the academic literature.

## Features

- **Retracted Paper Database**: Track papers that have been retracted, with expressions of concern, corrections, and other editorial notices
- **Citation Analysis**: Monitor how many times retracted papers continue to be cited after retraction
- **Advanced Search**: Filter by journal, subject, country, retraction reason, and more
- **Analytics Dashboard**: Visualize citation patterns, geographic distribution, and temporal trends
- **Real-time Data**: Regular updates from Retraction Watch and citation databases
- **API Access**: Programmatic access to data for researchers

## Quick Start

1. **Environment Setup**:
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

2. **Required Environment Variables**:
   - `SECRET_KEY`: Django secret key (generate a new one for production)
   - `DEBUG`: Set to `False` for production
   - `GOOGLE_ANALYTICS_ID`: Your GA4 measurement ID (optional)
   - `DATABASE_PASSWORD`: PostgreSQL password (if using PostgreSQL)

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Development Server**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Analytics Implementation

This application includes Google Analytics 4 (GA4) for tracking user interactions and research usage patterns:

### Setup
1. Copy `env.example` to `.env` in your project root
2. Add your GA4 Measurement ID to the `.env` file:
   ```
   GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
   ```
3. The analytics code is only loaded when both conditions are met:
   - `DEBUG=False` (production mode)
   - `GOOGLE_ANALYTICS_ID` is set and not empty

### Privacy Features
- IP anonymization enabled
- Google Signals disabled
- Ad personalization disabled
- Academic research-focused event tracking

### Tracked Events
- **Search Queries**: Track what researchers search for and result counts
- **Paper Views**: Monitor which retracted papers are accessed
- **Citation Analysis**: Track interactions with citation data
- **Dashboard Usage**: Monitor analytics dashboard engagement
- **External Links**: Track clicks to DOI and PubMed links

## ✨ Key Features

- **📊 Comprehensive Database**: Import and manage retracted papers from Retraction Watch
- **🔍 Advanced Search**: Full-text search with autocomplete and filtering
- **📈 Citation Tracking**: Fetch citations from OpenAlex, Semantic Scholar, and OpenCitations APIs
- **⚠️ Post-Retraction Analysis**: Track citations that occurred after retraction date
- **📊 Analytics Dashboard**: Visualize retraction trends and citation patterns
- **⏰ Automated Updates**: Daily scheduled refresh of papers and citations at 8:00 AM EST
- **🔄 Background Processing**: Celery-based task queue for reliable data processing
- **📱 Responsive Design**: Modern Bootstrap 5 UI that works on all devices
- **🚀 Easy Deployment**: Docker support for local development and cloud deployment

## 🕐 Automated Data Updates

The application automatically refreshes data daily:

- **8:00 AM EST (1:00 PM UTC)**: Refresh retracted papers from Retraction Watch
- **8:30 AM EST (1:30 PM UTC)**: Fetch new citations from academic APIs
- **2:00 AM EST Sundays**: Clean up old import logs

Tasks include automatic retry logic and comprehensive error handling.

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd CitingRetracted

# Start all services (web, database, Redis, Celery)
docker-compose up --build

# Initialize database and create admin user
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Set up scheduled tasks
docker-compose exec web python start_scheduler.py

# Import sample data (optional)
docker-compose exec web python manage.py import_retraction_watch data/sample.csv
```

Visit **http://localhost:8000** to access the application.

### Manual Installation

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed installation and deployment instructions.

## 📋 Management Commands

- `import_retraction_watch` - Import retracted papers from CSV
- `fetch_citations` - Fetch citation data from APIs
- `start_scheduler.py` - Set up automated daily tasks
- `test_scheduler.py` - Test scheduled tasks manually

See [management_commands.md](management_commands.md) for complete documentation.

## 🔧 Task Monitoring

Monitor scheduled tasks via:

- **Django Admin**: `/admin/django_celery_beat/`
- **Logs**: `docker-compose logs celery celery-beat`
- **Manual Testing**: `python test_scheduler.py`

## Data Sources

- **[Retraction Watch Database](https://retractionwatch.com/)**: Comprehensive database of retracted papers
- **[OpenAlex](https://openalex.org/)**: Primary source for citation data
- **[Semantic Scholar](https://www.semanticscholar.org/)**: Fallback citation source
- **[OpenCitations](https://opencitations.net/)**: Additional citation data

## Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CitingRetracted
   ```