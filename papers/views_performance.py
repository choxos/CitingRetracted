from django.shortcuts import render
from django.views.generic import View
from django.db.models import Q, Count, Avg, Sum, Max, F, Case, When, IntegerField
from django.db.models.functions import TruncYear, TruncMonth
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, date
import json
import logging

from .models import RetractedPaper, CitingPaper, Citation, DataImportLog

logger = logging.getLogger(__name__)

# Cache timeout constants
CACHE_TIMEOUT_SHORT = 300    # 5 minutes
CACHE_TIMEOUT_MEDIUM = 900   # 15 minutes 
CACHE_TIMEOUT_LONG = 3600    # 1 hour
CACHE_TIMEOUT_DAILY = 86400  # 24 hours

class PerformanceAnalyticsView(View):
    """Ultra-optimized analytics view with aggressive caching and minimal database queries"""
    template_name = 'papers/analytics.html'
    
    @method_decorator(cache_page(CACHE_TIMEOUT_MEDIUM))
    def get(self, request):
        context = self.get_cached_context()
        return render(request, self.template_name, context)
    
    def get_cached_context(self):
        """Get context with aggressive caching at multiple levels"""
        context = {}
        
        # Level 1: Basic stats (cached for 5 minutes)
        context.update(self._get_cached_basic_stats())
        
        # Level 2: Chart data (cached for 15 minutes)
        context.update(self._get_cached_chart_data())
        
        # Level 3: Complex analytics (cached for 1 hour)
        context.update(self._get_cached_complex_data())
        
        return context
    
    def _get_cached_basic_stats(self):
        """Basic statistics with short-term caching"""
        cache_key = 'analytics_basic_stats_v2'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            logger.info("Cache miss for basic stats - generating...")
            
            # Single optimized query for all basic statistics
            basic_stats = RetractedPaper.objects.aggregate(
                total_papers=Count('id'),
                recent_retractions=Count('id', filter=Q(
                    retraction_date__gte=timezone.now().date() - timedelta(days=365)
                )),
                avg_citations_per_paper=Avg('citation_count'),
                max_citations=Max('citation_count'),
                total_citation_sum=Sum('citation_count')
            )
            
            # Citation statistics in one query
            citation_stats = Citation.objects.aggregate(
                total_citations=Count('id'),
                post_retraction_citations=Count('id', filter=Q(days_after_retraction__gt=0)),
                pre_retraction_citations=Count('id', filter=Q(days_after_retraction__lt=0)),
                same_day_citations=Count('id', filter=Q(days_after_retraction=0))
            )
            
            # Calculate percentages
            total_citations = citation_stats['total_citations'] or 1
            basic_stats.update(citation_stats)
            basic_stats['post_retraction_percentage'] = (
                citation_stats['post_retraction_citations'] / total_citations
            ) * 100
            
            # Post-retraction timeline in one query
            post_retraction_timeline = Citation.objects.filter(
                days_after_retraction__gt=0
            ).aggregate(
                within_30_days=Count('id', filter=Q(days_after_retraction__lte=30)),
                within_6_months=Count('id', filter=Q(days_after_retraction__lte=180)),
                within_1_year=Count('id', filter=Q(days_after_retraction__lte=365)),
                within_2_years=Count('id', filter=Q(days_after_retraction__lte=730)),
                after_2_years=Count('id', filter=Q(days_after_retraction__gt=730))
            )
            
            cached_data = {
                'stats': basic_stats,
                'citation_patterns': {
                    'post_retraction': citation_stats['post_retraction_citations'],
                    'pre_retraction': citation_stats['pre_retraction_citations'],
                    'same_day': citation_stats['same_day_citations'],
                    'post_retraction_percentage': basic_stats['post_retraction_percentage']
                },
                'post_retraction_timeline': post_retraction_timeline
            }
            
            cache.set(cache_key, cached_data, CACHE_TIMEOUT_SHORT)
            logger.info("Basic stats cached successfully")
        
        return cached_data
    
    def _get_cached_chart_data(self):
        """Chart data with medium-term caching"""
        cache_key = 'analytics_chart_data_v2'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            logger.info("Cache miss for chart data - generating...")
            
            # Retraction trends (optimized with single query)
            retraction_trends_raw = list(RetractedPaper.objects.filter(
                retraction_date__isnull=False
            ).annotate(
                year=TruncYear('retraction_date')
            ).values('year').annotate(
                count=Count('id')
            ).order_by('year').values('year', 'count'))
            
            retraction_trends = [(item['year'].year, item['count']) for item in retraction_trends_raw]
            
            # Citation analysis (optimized with single query)
            citation_analysis_raw = list(Citation.objects.filter(
                citing_paper__publication_date__isnull=False
            ).annotate(
                year=TruncYear('citing_paper__publication_date')
            ).values('year').annotate(
                total_citations=Count('id'),
                post_retraction_citations=Count('id', filter=Q(days_after_retraction__gt=0)),
                pre_retraction_citations=Count('id', filter=Q(days_after_retraction__lt=0))
            ).order_by('year').values(
                'year', 'total_citations', 'post_retraction_citations', 'pre_retraction_citations'
            ))
            
            citation_analysis = [
                {
                    'year': item['year'].year,
                    'total_citations': item['total_citations'],
                    'post_retraction_citations': item['post_retraction_citations'],
                    'pre_retraction_citations': item['pre_retraction_citations']
                }
                for item in citation_analysis_raw
            ]
            
            # Subject distribution (optimized)
            subject_data = list(RetractedPaper.objects.exclude(
                subject__isnull=True
            ).exclude(
                subject__exact=''
            ).values('subject').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('subject', 'count'))
            
            cached_data = {
                'retraction_trends_by_year': [
                    {'year': year, 'count': count} for year, count in retraction_trends
                ],
                'citation_analysis_by_year': citation_analysis,
                'subject_donut_data': [
                    {'subject': subject[:30], 'count': count} for subject, count in subject_data
                ]
            }
            
            cache.set(cache_key, cached_data, CACHE_TIMEOUT_MEDIUM)
            logger.info("Chart data cached successfully")
        
        return cached_data
    
    def _get_cached_complex_data(self):
        """Complex analytics with long-term caching"""
        cache_key = 'analytics_complex_data_v2'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            logger.info("Cache miss for complex data - generating...")
            
            # Problematic papers (pre-computed and cached)
            problematic_papers = list(RetractedPaper.objects.select_related().annotate(
                post_retraction_count=Count('citations', filter=Q(citations__days_after_retraction__gt=0))
            ).filter(
                post_retraction_count__gt=0
            ).order_by('-post_retraction_count')[:10].values(
                'record_id', 'title', 'journal', 'retraction_date', 'post_retraction_count', 'citation_count'
            ))
            
            # Journal analysis (optimized)
            journal_data = list(RetractedPaper.objects.exclude(
                journal__isnull=True
            ).exclude(
                journal__exact=''
            ).values('journal').annotate(
                retraction_count=Count('id'),
                avg_citations=Avg('citation_count')
            ).order_by('-retraction_count')[:10].values(
                'journal', 'retraction_count', 'avg_citations'
            ))
            
            # Country analysis (simplified and cached)
            country_data = list(RetractedPaper.objects.exclude(
                country__isnull=True
            ).exclude(
                country__exact=''
            ).values('country').annotate(
                count=Count('id')
            ).order_by('-count')[:20].values_list('country', 'count'))
            
            # Sunburst data (simplified)
            sunburst_data = self._generate_sunburst_data()
            
            cached_data = {
                'problematic_papers_detailed': [
                    {
                        'record_id': p['record_id'],
                        'title': p['title'],
                        'journal': p['journal'] or 'Unknown',
                        'retraction_date': p['retraction_date'],
                        'post_retraction_citations': p['post_retraction_count'],
                        'total_citations': p['citation_count'] or 0,
                        'citation_rate': (p['post_retraction_count'] / max(p['citation_count'], 1)) * 100
                    }
                    for p in problematic_papers
                ],
                'journal_bubble_data': [
                    {
                        'journal': j['journal'][:30],
                        'x': j['retraction_count'],
                        'y': j['avg_citations'] or 0,
                        'size': min(j['retraction_count'] * 2, 50),
                        'impact_score': j['avg_citations'] or 0
                    }
                    for j in journal_data
                ],
                'country_analytics': [
                    {'country': country, 'count': count} for country, count in country_data
                ],
                'sunburst_data': sunburst_data
            }
            
            cache.set(cache_key, cached_data, CACHE_TIMEOUT_LONG)
            logger.info("Complex data cached successfully")
        
        return cached_data
    
    def _generate_sunburst_data(self):
        """Generate optimized sunburst data"""
        # Get subject counts directly
        subjects = RetractedPaper.objects.exclude(
            subject__isnull=True
        ).exclude(
            subject__exact=''
        ).values_list('subject', flat=True)
        
        # Parse subjects and count
        category_counts = {}
        for subject_string in subjects:
            # Simple parsing - take first subject if multiple
            first_subject = subject_string.split(';')[0].strip()
            category_counts[first_subject] = category_counts.get(first_subject, 0) + 1
        
        # Convert to sunburst format
        children = [
            {'name': subject, 'value': count, 'full_name': subject}
            for subject, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            'name': 'Subject Areas',
            'value': sum(category_counts.values()),
            'children': children[:15]  # Limit for performance
        }

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor database query performance"""
    def wrapper(*args, **kwargs):
        from django.db import connection
        queries_before = len(connection.queries)
        start_time = timezone.now()
        
        result = func(*args, **kwargs)
        
        end_time = timezone.now()
        queries_after = len(connection.queries)
        
        logger.info(f"{func.__name__} executed in {(end_time - start_time).total_seconds():.2f}s with {queries_after - queries_before} queries")
        return result
    return wrapper 