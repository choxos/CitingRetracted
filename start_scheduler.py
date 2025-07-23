#!/usr/bin/env python
"""
Setup script to initialize scheduled tasks for CitingRetracted.
Run this once after deployment to set up the daily refresh schedule.
"""

import os
import sys
import django
from datetime import time

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

def setup_scheduled_tasks():
    """Setup the daily scheduled tasks for data refresh."""
    
    # Create crontab schedules for 8:00 AM and 8:30 AM EST (1:00 PM and 1:30 PM UTC)
    schedule_8am, created = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=13,  # 1:00 PM UTC = 8:00 AM EST
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='UTC'
    )
    
    schedule_830am, created = CrontabSchedule.objects.get_or_create(
        minute=30,
        hour=13,  # 1:30 PM UTC = 8:30 AM EST
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='UTC'
    )
    
    # Create periodic task for retracted papers refresh
    papers_task, created = PeriodicTask.objects.get_or_create(
        name='Daily Retracted Papers Refresh',
        defaults={
            'crontab': schedule_8am,
            'task': 'papers.tasks.refresh_retracted_papers',
            'enabled': True,
            'description': 'Daily refresh of retracted papers from Retraction Watch at 8:00 AM EST'
        }
    )
    
    if created:
        print("✅ Created scheduled task: Daily Retracted Papers Refresh (8:00 AM EST)")
    else:
        print("ℹ️  Scheduled task already exists: Daily Retracted Papers Refresh")
    
    # Create periodic task for citations refresh
    citations_task, created = PeriodicTask.objects.get_or_create(
        name='Daily Citations Refresh',
        defaults={
            'crontab': schedule_830am,
            'task': 'papers.tasks.refresh_citations',
            'enabled': True,
            'description': 'Daily refresh of citation data at 8:30 AM EST'
        }
    )
    
    if created:
        print("✅ Created scheduled task: Daily Citations Refresh (8:30 AM EST)")
    else:
        print("ℹ️  Scheduled task already exists: Daily Citations Refresh")
    
    # Create weekly cleanup task (Sundays at 2:00 AM EST = 7:00 AM UTC)
    cleanup_schedule, created = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=7,  # 7:00 AM UTC = 2:00 AM EST
        day_of_week=0,  # Sunday
        day_of_month='*',
        month_of_year='*',
        timezone='UTC'
    )
    
    cleanup_task, created = PeriodicTask.objects.get_or_create(
        name='Weekly Cleanup',
        defaults={
            'crontab': cleanup_schedule,
            'task': 'papers.tasks.cleanup_old_logs',
            'enabled': True,
            'description': 'Weekly cleanup of old import logs (Sundays at 2:00 AM EST)'
        }
    )
    
    if created:
        print("✅ Created scheduled task: Weekly Cleanup (Sundays at 2:00 AM EST)")
    else:
        print("ℹ️  Scheduled task already exists: Weekly Cleanup")
    
    print("\n🎯 All scheduled tasks configured successfully!")
    print("\nScheduled Tasks Summary:")
    print("- 📅 8:00 AM EST Daily: Refresh retracted papers")
    print("- 📅 8:30 AM EST Daily: Refresh citations")
    print("- 📅 2:00 AM EST Sundays: Cleanup old logs")
    print("\nTo view and manage tasks:")
    print("- Django Admin: /admin/django_celery_beat/")
    print("- Monitor logs: docker-compose logs celery-beat")

if __name__ == '__main__':
    setup_scheduled_tasks() 