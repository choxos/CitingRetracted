# 🕐 Automated Scheduler Setup

The CitingRetracted application now includes automated daily refresh functionality using Celery and Celery Beat.

## ✅ What Was Added

### **1. Celery Integration**
- **Celery Worker**: Handles background task execution
- **Celery Beat**: Manages scheduled task execution
- **Redis**: Used as message broker and result backend
- **Django-Celery-Beat**: Database-backed task scheduler

### **2. Scheduled Tasks**
- **Daily Retracted Papers Refresh** - 8:00 AM EST (1:00 PM UTC)
- **Daily Citations Refresh** - 8:30 AM EST (1:30 PM UTC)  
- **Weekly Cleanup** - Sundays at 2:00 AM EST (7:00 AM UTC)

### **3. New Files Created**
- `citing_retracted/celery.py` - Celery configuration
- `papers/tasks.py` - Scheduled task definitions
- `start_scheduler.py` - One-time setup script
- `test_scheduler.py` - Testing and validation script
- `management_commands.md` - Complete command documentation

### **4. Updated Files**
- `requirements.txt` - Added Celery dependencies
- `citing_retracted/settings.py` - Celery configuration
- `docker-compose.yml` - Added celery-beat service
- `DEPLOYMENT.md` - Added scheduler documentation
- `README.md` - Updated with scheduler features

## 🚀 How to Use

### **1. Development (Docker Compose)**
```bash
# Start all services including scheduler
docker-compose up --build

# Set up scheduled tasks (run once)
docker-compose exec web python start_scheduler.py

# Test scheduler functionality
docker-compose exec web python test_scheduler.py
```

### **2. Manual Task Testing**
```bash
# Test connectivity and view scheduled tasks
python test_scheduler.py

# Run tasks immediately
python manage.py shell
>>> from papers.tasks import refresh_retracted_papers, refresh_citations
>>> refresh_retracted_papers.delay()
>>> refresh_citations.delay()
```

### **3. Monitor Tasks**
```bash
# View worker logs
docker-compose logs celery

# View scheduler logs  
docker-compose logs celery-beat

# Django admin interface
http://localhost:8000/admin/django_celery_beat/
```

## ⚙️ Task Details

### **Refresh Retracted Papers Task**
- **Schedule**: Daily at 8:00 AM EST
- **Function**: Imports new/updated retracted papers from Retraction Watch
- **Features**: 
  - Updates existing papers with new information
  - Automatic retry with exponential backoff
  - Comprehensive error logging

### **Refresh Citations Task**
- **Schedule**: Daily at 8:30 AM EST (staggered 30 minutes)
- **Function**: Fetches new citations from academic APIs
- **Features**:
  - Processes up to 100 papers per run to respect API limits
  - Multi-API fallback (OpenAlex → Semantic Scholar → OpenCitations)
  - Rate limiting and error handling

### **Weekly Cleanup Task**
- **Schedule**: Sundays at 2:00 AM EST
- **Function**: Removes old import logs (30+ days)
- **Purpose**: Maintains database performance and storage

## 🔧 Production Considerations

### **Scaling**
- Run multiple Celery workers for parallel processing
- Use separate queues for different task types
- Monitor memory usage (100-500MB per worker)

### **Monitoring**
- Set up log aggregation for task monitoring
- Configure alerts for task failures
- Use Flower for real-time Celery monitoring

### **Security**
- Secure Redis with authentication
- Use environment variables for sensitive configuration
- Implement proper logging retention policies

## 🛠 Troubleshooting

### **Common Issues**

1. **Redis Connection Error**
   ```bash
   redis-cli ping  # Test Redis connectivity
   ```

2. **Tasks Not Running**
   ```bash
   celery -A citing_retracted inspect ping  # Check workers
   celery -A citing_retracted inspect scheduled  # Check schedule
   ```

3. **Database Lock During Migration**
   ```bash
   docker-compose stop celery celery-beat
   python manage.py migrate
   docker-compose start celery celery-beat
   ```

### **Debug Mode**
Set `CELERY_TASK_ALWAYS_EAGER=True` for synchronous task execution during development.

## ✨ Benefits

1. **🔄 Automatic Updates**: Data stays fresh without manual intervention
2. **⚡ Reliability**: Built-in retry logic and error handling
3. **📊 Monitoring**: Full visibility into task execution
4. **🎯 Efficiency**: Staggered scheduling prevents API overload
5. **🔧 Flexibility**: Easy to modify schedules via Django admin

## 🎯 Next Steps

The scheduler is now fully operational! The application will automatically:
- Keep retracted papers data current
- Fetch new citations daily
- Maintain database performance
- Log all operations for monitoring

Access the admin interface at `/admin/django_celery_beat/` to view and manage scheduled tasks. 