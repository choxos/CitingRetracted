from django.core.cache import cache, caches
from django.conf import settings
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from functools import wraps
import hashlib
import json
from datetime import timedelta

def get_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key from arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"{prefix}:{key_hash}"

def cached_function(timeout=300, cache_alias='default', key_prefix=''):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_obj = caches[cache_alias]
            cache_key = get_cache_key(key_prefix or func.__name__, *args, **kwargs)
            
            result = cache_obj.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache_obj.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

@cached_function(timeout=3600, cache_alias='analytics', key_prefix='analytics_overview')
def get_analytics_overview():
    """Get cached analytics overview data"""
    from papers.models import RetractedPaper, Citation, CitingPaper
    
    total_papers = RetractedPaper.objects.count()
    total_citations = Citation.objects.count()
    total_citing_papers = CitingPaper.objects.count()
    
    # Post-retraction citations
    post_retraction_citations = Citation.objects.filter(
        days_after_retraction__gt=0
    ).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_papers = RetractedPaper.objects.filter(
        retraction_date__gte=thirty_days_ago
    ).count()
    
    # Top subjects
    top_subjects = list(RetractedPaper.objects.exclude(
        subject__isnull=True
    ).exclude(
        subject__exact=''
    ).values('subject').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    return {
        'total_papers': total_papers,
        'total_citations': total_citations,
        'total_citing_papers': total_citing_papers,
        'post_retraction_citations': post_retraction_citations,
        'post_retraction_rate': (post_retraction_citations / total_citations * 100) if total_citations > 0 else 0,
        'recent_papers': recent_papers,
        'top_subjects': top_subjects,
        'cache_timestamp': timezone.now().isoformat()
    }

@cached_function(timeout=1800, cache_alias='analytics', key_prefix='retraction_trends')
def get_retraction_trends():
    """Get cached retraction trends data"""
    from papers.models import RetractedPaper
    from django.db.models import TruncYear
    
    return list(RetractedPaper.objects.exclude(
        retraction_date__isnull=True
    ).annotate(
        year=TruncYear('retraction_date')
    ).values('year').annotate(
        count=Count('id')
    ).order_by('year'))

@cached_function(timeout=1800, cache_alias='analytics', key_prefix='citation_analysis')
def get_citation_analysis():
    """Get cached citation analysis data"""
    from papers.models import Citation, RetractedPaper
    from django.db.models import TruncYear
    
    # Citation trends by year
    citation_trends = list(Citation.objects.exclude(
        citation_date__isnull=True
    ).annotate(
        year=TruncYear('citation_date')
    ).values('year').annotate(
        total=Count('id'),
        pre_retraction=Count('id', filter=Q(days_after_retraction__lt=0)),
        post_retraction=Count('id', filter=Q(days_after_retraction__gt=0))
    ).order_by('year'))
    
    # Citation timing distribution
    timing_data = list(Citation.objects.exclude(
        days_after_retraction__isnull=True
    ).extra(
        select={
            'time_bucket': 'CASE '
                         'WHEN days_after_retraction < -365 THEN "Before (-1Y+)"'
                         'WHEN days_after_retraction < 0 THEN "Before Retraction"'
                         'WHEN days_after_retraction < 30 THEN "After (0-30 days)"'
                         'WHEN days_after_retraction < 365 THEN "After (30-365 days)"'
                         'ELSE "After (1Y+)" END'
        }
    ).values('time_bucket').annotate(
        count=Count('id')
    ).order_by('time_bucket'))
    
    return {
        'citation_trends': citation_trends,
        'timing_distribution': timing_data
    }

@cached_function(timeout=3600, cache_alias='analytics', key_prefix='subject_analysis')
def get_subject_analysis():
    """Get cached subject analysis data"""
    from papers.models import RetractedPaper
    
    # Subject distribution
    subjects = list(RetractedPaper.objects.exclude(
        subject__isnull=True
    ).exclude(
        subject__exact=''
    ).values('subject').annotate(
        count=Count('id'),
        avg_citations=Avg('citation_count')
    ).order_by('-count')[:20])
    
    # Broad subjects
    broad_subjects = list(RetractedPaper.objects.exclude(
        broad_subjects__isnull=True
    ).exclude(
        broad_subjects__exact=''
    ).values('broad_subjects').annotate(
        count=Count('id')
    ).order_by('-count')[:15])
    
    return {
        'subjects': subjects,
        'broad_subjects': broad_subjects
    }

@cached_function(timeout=3600, cache_alias='analytics', key_prefix='geographic_analysis')
def get_geographic_analysis():
    """Get cached geographic analysis data"""
    from papers.models import RetractedPaper
    
    countries = list(RetractedPaper.objects.exclude(
        country__isnull=True
    ).exclude(
        country__exact=''
    ).values('country').annotate(
        count=Count('id'),
        open_access_count=Count('id', filter=Q(is_open_access=True)),
        avg_citations=Avg('citation_count')
    ).order_by('-count')[:50])
    
    # Add open access percentage
    for country in countries:
        if country['count'] > 0:
            country['open_access_percentage'] = (
                country['open_access_count'] / country['count'] * 100
            )
        else:
            country['open_access_percentage'] = 0
    
    return countries

@cached_function(timeout=1800, cache_alias='analytics', key_prefix='journal_analysis')
def get_journal_analysis():
    """Get cached journal analysis data"""
    from papers.models import RetractedPaper
    
    return list(RetractedPaper.objects.exclude(
        journal__isnull=True
    ).exclude(
        journal__exact=''
    ).values('journal', 'publisher').annotate(
        count=Count('id'),
        avg_citations=Avg('citation_count'),
        open_access_rate=Avg('is_open_access')
    ).order_by('-count')[:30])

def invalidate_analytics_cache():
    """Invalidate all analytics cache"""
    analytics_cache = caches['analytics']
    analytics_cache.clear()

def get_paginated_queryset(queryset, page, per_page=25):
    """Get paginated queryset with caching"""
    cache_key = f"paginated:{queryset.model._meta.label}:{page}:{per_page}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Calculate pagination
    start = (page - 1) * per_page
    end = start + per_page
    
    items = list(queryset[start:end])
    total_count = queryset.count()
    
    result = {
        'items': items,
        'total_count': total_count,
        'has_next': end < total_count,
        'has_previous': page > 1,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, result, 300)
    return result

class CacheWarmer:
    """Utility for warming up caches"""
    
    @staticmethod
    def warm_analytics_cache():
        """Warm up all analytics caches"""
        print("Warming analytics cache...")
        get_analytics_overview()
        get_retraction_trends()
        get_citation_analysis()
        get_subject_analysis()
        get_geographic_analysis()
        get_journal_analysis()
        print("Analytics cache warmed successfully!")
    
    @staticmethod
    def warm_all_caches():
        """Warm up all application caches"""
        CacheWarmer.warm_analytics_cache()
        print("All caches warmed successfully!") 