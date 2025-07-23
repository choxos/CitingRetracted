from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def refresh_retracted_papers(self):
    """
    Scheduled task to refresh retracted papers data from Retraction Watch.
    Runs daily at 8:00 AM EST (1:00 PM UTC).
    """
    try:
        logger.info("Starting scheduled refresh of retracted papers...")
        
        # Import new/updated retracted papers from Retraction Watch
        call_command(
            'import_retraction_watch',
            '--update-existing',
            verbosity=1
        )
        
        logger.info("Successfully completed retracted papers refresh")
        return "Retracted papers refresh completed successfully"
        
    except Exception as exc:
        logger.error(f"Error in retracted papers refresh: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@shared_task(bind=True)
def refresh_citations(self):
    """
    Scheduled task to refresh citation data for retracted papers.
    Runs daily at 8:30 AM EST (1:30 PM UTC).
    """
    try:
        logger.info("Starting scheduled refresh of citations...")
        
        # Fetch new citations for retracted papers
        call_command(
            'fetch_citations',
            '--limit', '100',  # Process 100 papers per run to avoid API limits
            verbosity=1
        )
        
        logger.info("Successfully completed citations refresh")
        return "Citations refresh completed successfully"
        
    except Exception as exc:
        logger.error(f"Error in citations refresh: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=120, max_retries=3)

@shared_task
def refresh_citations_for_paper(paper_id):
    """
    Task to refresh citations for a specific retracted paper.
    Can be called manually or from other tasks.
    """
    try:
        from .models import RetractedPaper
        
        paper = RetractedPaper.objects.get(id=paper_id)
        logger.info(f"Refreshing citations for paper: {paper.title[:50]}...")
        
        # Fetch citations for specific paper
        call_command(
            'fetch_citations',
            '--paper-id', str(paper_id),
            verbosity=1
        )
        
        logger.info(f"Successfully refreshed citations for paper ID {paper_id}")
        return f"Citations refreshed for paper ID {paper_id}"
        
    except Exception as exc:
        logger.error(f"Error refreshing citations for paper {paper_id}: {exc}")
        raise exc

@shared_task
def cleanup_old_logs():
    """
    Task to clean up old data import logs (keep last 30 days).
    Runs weekly to maintain database performance.
    """
    try:
        from .models import DataImportLog
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = DataImportLog.objects.filter(created_at__lt=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old import logs")
        return f"Cleaned up {deleted_count} old import logs"
        
    except Exception as exc:
        logger.error(f"Error in cleanup task: {exc}")
        raise exc 