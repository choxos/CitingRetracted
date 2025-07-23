#!/usr/bin/env python
"""
Test script to manually trigger scheduled tasks for testing.
Use this to verify that your scheduled tasks work correctly.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')
django.setup()

from papers.tasks import refresh_retracted_papers, refresh_citations, cleanup_old_logs
from celery import current_app

def test_task_connectivity():
    """Test if Celery is working and tasks are discoverable."""
    print("🔍 Testing Celery connectivity...")
    
    try:
        # Check if tasks are registered
        registered_tasks = list(current_app.tasks.keys())
        paper_tasks = [task for task in registered_tasks if 'papers.tasks' in task]
        
        print(f"✅ Found {len(paper_tasks)} paper-related tasks:")
        for task in paper_tasks:
            print(f"   - {task}")
        
        return True
    except Exception as e:
        print(f"❌ Error connecting to Celery: {e}")
        return False

def test_tasks_manually():
    """Run tasks manually to test functionality."""
    print("\n🧪 Testing tasks manually...")
    
    try:
        print("1. Testing retracted papers refresh...")
        result = refresh_retracted_papers.delay()
        print(f"   ✅ Task queued with ID: {result.id}")
        print(f"   Status: {result.status}")
        
        print("\n2. Testing citations refresh...")
        result = refresh_citations.delay()
        print(f"   ✅ Task queued with ID: {result.id}")
        print(f"   Status: {result.status}")
        
        print("\n3. Testing cleanup task...")
        result = cleanup_old_logs.delay()
        print(f"   ✅ Task queued with ID: {result.id}")
        print(f"   Status: {result.status}")
        
        print("\n✨ All tasks queued successfully!")
        print("💡 Monitor task execution with: docker-compose logs celery")
        
    except Exception as e:
        print(f"❌ Error running tasks: {e}")
        print("💡 Make sure Redis and Celery worker are running:")
        print("   docker-compose up redis celery")

def check_scheduled_tasks():
    """Check the scheduled tasks in the database."""
    print("\n📅 Checking scheduled tasks...")
    
    try:
        from django_celery_beat.models import PeriodicTask
        
        tasks = PeriodicTask.objects.all()
        print(f"Found {tasks.count()} scheduled tasks:")
        
        for task in tasks:
            status = "✅ Enabled" if task.enabled else "❌ Disabled"
            print(f"   {status} {task.name}")
            print(f"      Task: {task.task}")
            print(f"      Schedule: {task.crontab}")
            print()
            
    except Exception as e:
        print(f"❌ Error checking scheduled tasks: {e}")

def main():
    """Main test function."""
    print("🚀 CitingRetracted Scheduler Test")
    print("=" * 40)
    
    # Test 1: Check Celery connectivity
    if not test_task_connectivity():
        print("\n❌ Celery connectivity test failed")
        return
    
    # Test 2: Check scheduled tasks
    check_scheduled_tasks()
    
    # Test 3: Manual task execution
    choice = input("\nDo you want to run tasks manually? (y/N): ").lower()
    if choice in ['y', 'yes']:
        test_tasks_manually()
    else:
        print("Skipping manual task execution")
    
    print("\n🎯 Test completed!")
    print("\nNext steps:")
    print("1. Start Celery worker: docker-compose up celery")
    print("2. Start Celery beat: docker-compose up celery-beat")
    print("3. Monitor logs: docker-compose logs -f celery celery-beat")
    print("4. View admin: http://localhost:8000/admin/django_celery_beat/")

if __name__ == '__main__':
    main() 