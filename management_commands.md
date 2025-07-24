# Django Management Commands

This document explains all available Django management commands for the Post-Retraction Citation Tracker (PRCT) application.

## Data Import Commands

### `import_retraction_watch`

Import retracted papers from Retraction Watch CSV data.

**Usage:**
```bash
python manage.py import_retraction_watch [CSV_FILE_PATH] [OPTIONS]
```

**Options:**
- `--dry-run`: Preview changes without saving to database
- `--limit N`: Process only first N rows
- `--update-existing`: Update existing papers with new data

**Examples:**
```bash
# Import from CSV file
python manage.py import_retraction_watch data/retractionwatch_data.csv

# Dry run to preview changes
python manage.py import_retraction_watch data/retractionwatch_data.csv --dry-run

# Update existing papers
python manage.py import_retraction_watch data/retractionwatch_data.csv --update-existing

# Process only first 100 rows
python manage.py import_retraction_watch data/retractionwatch_data.csv --limit 100
```

### `fetch_citations`

Fetch citation data for retracted papers using multiple APIs.

**Usage:**
```bash
python manage.py fetch_citations [OPTIONS]
```

**Options:**
- `--dry-run`: Preview API calls without saving data
- `--limit N`: Process maximum N papers
- `--paper-id ID`: Fetch citations for specific paper ID

**Examples:**
```bash
# Fetch citations for papers needing updates
python manage.py fetch_citations

# Fetch for specific paper
python manage.py fetch_citations --paper-id 123

# Dry run with limit
python manage.py fetch_citations --dry-run --limit 10

# Process 50 papers maximum
python manage.py fetch_citations --limit 50
```

## Scheduled Tasks (Celery)

### Automatic Daily Refresh

The application automatically refreshes data daily at **8:00 AM EST**:

1. **8:00 AM EST:** Refresh retracted papers (`refresh_retracted_papers`)
2. **8:30 AM EST:** Fetch new citations (`refresh_citations`)

### Manual Task Execution

**Run tasks manually via Django shell:**
```python
from papers.tasks import refresh_retracted_papers, refresh_citations, cleanup_old_logs

# Run immediately
result = refresh_retracted_papers.delay()
print(f"Task ID: {result.id}")

# Check task status
print(result.status)
print(result.result)
```

**Monitor via Celery commands:**
```bash
# View active tasks
celery -A citing_retracted inspect active

# View worker stats
celery -A citing_retracted inspect stats

# View scheduled tasks
celery -A citing_retracted inspect scheduled
```

### Available Tasks

1. **`refresh_retracted_papers`**
   - Updates retracted papers from Retraction Watch
   - Runs daily at 8:00 AM EST
   - Includes retry logic with exponential backoff

2. **`refresh_citations`**
   - Fetches new citations for papers
   - Runs daily at 8:30 AM EST
   - Processes up to 100 papers per run

3. **`refresh_citations_for_paper(paper_id)`**
   - Refresh citations for specific paper
   - Can be called manually or from other tasks

4. **`cleanup_old_logs`**
   - Removes import logs older than 30 days
   - Runs weekly to maintain performance

## Task Monitoring

### Django Admin Interface

Access task management at `/admin/django_celery_beat/`:

- **Periodic Tasks:** View and modify scheduled tasks
- **Intervals:** Configure task intervals
- **Crontabs:** Set up cron-style schedules
- **Task Results:** Monitor task execution history

### Logging

Task execution is logged with different levels:

```python
# View task logs
import logging
logging.getLogger('papers.tasks').setLevel(logging.INFO)
```

**Log locations:**
- Docker: `docker-compose logs celery`
- Local: Console output or log files

### Error Handling

Tasks include built-in error handling:

- **Automatic Retries:** Up to 3 retries with exponential backoff
- **Error Logging:** Detailed error messages in logs
- **Graceful Degradation:** Tasks continue even if some operations fail

## Production Considerations

### Scaling Workers

```bash
# Run multiple worker processes
celery -A citing_retracted worker --concurrency=4

# Separate queues for different task types
celery -A citing_retracted worker -Q citations,maintenance
```

### Monitoring

```bash
# Real-time monitoring
celery -A citing_retracted events

# Flower web interface (install flower first)
celery -A citing_retracted flower
```

### Resource Management

- **Memory:** Each worker can consume 100-500MB RAM
- **API Limits:** Citation fetching respects API rate limits
- **Database:** Tasks use connection pooling

## Troubleshooting

### Common Issues

1. **Redis Connection Error:**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Restart Redis
   sudo systemctl restart redis
   ```

2. **Task Not Running:**
   ```bash
   # Check worker status
   celery -A citing_retracted inspect ping
   
   # Check scheduled tasks
   celery -A citing_retracted inspect scheduled
   ```

3. **Database Lock Issues:**
   ```bash
   # Stop all workers before migrations
   docker-compose stop celery celery-beat
   python manage.py migrate
   docker-compose start celery celery-beat
   ```

### Debug Mode

For development, set `CELERY_TASK_ALWAYS_EAGER=True` to run tasks synchronously:

```bash
export CELERY_TASK_ALWAYS_EAGER=true
python manage.py runserver
```

This executes tasks immediately without Celery worker. 