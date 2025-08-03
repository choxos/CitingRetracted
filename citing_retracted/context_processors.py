"""
Context processors for citing_retracted project.
"""
import os


def analytics_context(request):
    """
    Add Google Analytics configuration to all template contexts.
    """
    return {
        'google_analytics_id': os.getenv('GOOGLE_ANALYTICS_ID', ''),
        'debug': os.getenv('DEBUG', 'True').lower() == 'true',
    } 