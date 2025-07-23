# Citing Retracted Papers Database

A comprehensive web application built with Django to track retracted scientific papers and analyze their citation patterns. This tool helps researchers identify potential issues in academic literature by showing which retracted papers are still being cited in current research.

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

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Web interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## 🚀 Deployment

For detailed deployment instructions to various platforms, see [DEPLOYMENT.md](DEPLOYMENT.md):

- **Local Development**: Docker Compose setup
- **Google Cloud Platform**: App Engine and Cloud Run
- **Railway**: GitHub integration and CLI deployment
- **Production optimizations**: Redis, Celery, security settings

## Data Import

### Import Retracted Papers

Import data from the Retraction Watch CSV:

```bash
# Download and import automatically
python3 manage.py import_retraction_watch

# Import from local file
python3 manage.py import_retraction_watch --file /path/to/retraction_watch.csv

# Dry run to see what would be imported
python3 manage.py import_retraction_watch --dry-run --limit 10

# Update existing records
python3 manage.py import_retraction_watch --update-existing
```

### Fetch Citation Data

Retrieve citation information from APIs:

```bash
# Fetch citations for all papers
python3 manage.py fetch_citations

# Fetch for specific paper
python3 manage.py fetch_citations --paper-id RW12345

# Limit processing for testing
python3 manage.py fetch_citations --limit 10

# Force refresh even for recently checked papers
python3 manage.py fetch_citations --force-refresh
```

## Configuration

### Environment Variables

Create a `.env` file for production settings:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### API Settings

The application includes rate limiting for external APIs. Adjust in `settings.py`:

```python
API_RATE_LIMITS = {
    'openalex': {
        'requests_per_second': 10,
        'requests_per_day': 100000,
    },
    'semantic_scholar': {
        'requests_per_second': 1,
        'requests_per_day': 1000,
    },
}
```

## Database Schema

### Core Models

- **RetractedPaper**: Stores retracted paper information
- **CitingPaper**: Papers that cite retracted papers
- **Citation**: Links between retracted and citing papers
- **DataImportLog**: Tracks data import operations

### Key Fields

- `record_id`: Unique identifier from Retraction Watch
- `original_paper_doi`: DOI of the retracted paper
- `retraction_date`: Date of retraction
- `citation_count`: Cached count of citations
- `days_after_retraction`: Timeline analysis field

## API Endpoints

### REST API

- `/api/search-autocomplete/`: Search suggestions
- `/api/paper/<record_id>/citations/`: Citation data for charts
- `/api/export/`: Data export functionality

### Usage Examples

```javascript
// Get citation data for charts
fetch('/api/paper/RW12345/citations/')
    .then(response => response.json())
    .then(data => {
        console.log(data.citations_by_year);
        console.log(data.timeline_data);
    });
```

## Development

### Project Structure

```
CitingRetracted/
├── papers/                 # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # Web views
│   ├── admin.py           # Admin interface
│   ├── management/        # Management commands
│   └── utils/            # API clients and utilities
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── citing_retracted/    # Django project settings
└── requirements.txt     # Python dependencies
```

### Running Tests

```bash
python manage.py test
```

### Code Style

The project follows Django best practices:
- PEP 8 style guide
- Django naming conventions
- Comprehensive docstrings
- Type hints where appropriate

## Deployment

### Production Settings

1. **Database**: Use PostgreSQL for full-text search capabilities
2. **Static Files**: Configure with WhiteNoise or CDN
3. **Caching**: Use Redis for production caching
4. **Background Tasks**: Set up Celery for citation fetching

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "citing_retracted.wsgi:application"]
```

## Contributing

### Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Retraction Watch** for providing the comprehensive retracted papers database
- **OpenAlex** for open access to citation data
- **Django Community** for the excellent web framework
- **Bootstrap** for the responsive UI components

## Support

### Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [OpenAlex API](https://docs.openalex.org/)
- [Retraction Watch](https://retractionwatch.com/)

### Issues

If you encounter any problems or have suggestions, please create an issue on the project repository.

### Data Updates

The database should be updated regularly:
- Weekly import of new retractions
- Monthly refresh of citation data
- Quarterly validation of data integrity

---

**Built with ❤️ for the research community**