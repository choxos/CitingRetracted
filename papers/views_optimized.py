from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, Prefetch
from django.core.cache import cache
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import RetractedPaper, Citation, CitingPaper
from .utils.cache_utils import (
    get_analytics_overview, get_retraction_trends, get_citation_analysis,
    get_subject_analysis, get_geographic_analysis, get_journal_analysis,
    get_paginated_queryset, cached_function
)

# ============================================================================
# OPTIMIZED HOME VIEW
# ============================================================================

@method_decorator(cache_page(300), name='dispatch')  # 5 minute cache
class OptimizedHomeView(ListView):
    """Optimized home view with caching and efficient queries"""
    model = RetractedPaper
    template_name = 'papers/home.html'
    context_object_name = 'recent_papers'
    paginate_by = 10
    
    def get_queryset(self):
        """Optimized queryset with select_related and prefetch_related"""
        return RetractedPaper.objects.select_related().prefetch_related(
            Prefetch('citation_set', 
                    queryset=Citation.objects.select_related('citing_paper'))
        ).order_by('-retraction_date')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use cached analytics overview
        overview_data = get_analytics_overview()
        context.update(overview_data)
        
        # Recent citations with optimization
        recent_citations = Citation.objects.select_related(
            'retracted_paper', 'citing_paper'
        ).order_by('-id')[:5]
        
        context.update({
            'recent_citations': recent_citations,
            'show_search_form': True,
        })
        
        return context

# ============================================================================
# OPTIMIZED ANALYTICS VIEW
# ============================================================================

@method_decorator(cache_page(900), name='dispatch')  # 15 minute cache
class OptimizedAnalyticsView(ListView):
    """Highly optimized analytics view with extensive caching"""
    model = RetractedPaper
    template_name = 'papers/analytics.html'
    context_object_name = 'papers'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use all cached analytics functions
        context.update({
            'analytics_overview': get_analytics_overview(),
            'retraction_years': get_retraction_trends(),
            'retraction_comparison': get_citation_analysis()['citation_trends'],
            'citation_timing': get_citation_analysis()['timing_distribution'],
            'subject_data': get_subject_analysis(),
            'country_analytics': get_geographic_analysis(),
            'journal_analytics': get_journal_analysis(),
            'world_map_data': get_geographic_analysis(),
        })
        
        # Prepare data for charts (optimized)
        self._prepare_chart_data(context)
        
        return context
    
    def _prepare_chart_data(self, context):
        """Prepare optimized data for JavaScript charts"""
        
        # Sunburst data (cached)
        sunburst_data = self._get_sunburst_data()
        context['sunburst_data'] = sunburst_data
        
        # Network data (simplified for performance)
        network_data = self._get_network_data()
        context['network_data'] = network_data
        
        # Problematic papers (cached and limited)
        problematic_papers = self._get_problematic_papers()
        context['problematic_papers_detailed'] = problematic_papers
    
    @cached_function(timeout=3600, cache_alias='analytics', key_prefix='sunburst_data')
    def _get_sunburst_data(self):
        """Generate sunburst chart data with caching"""
        from collections import defaultdict
        
        # Get broad subjects and specific fields
        papers_with_subjects = RetractedPaper.objects.exclude(
            broad_subjects__isnull=True
        ).exclude(
            broad_subjects__exact=''
        ).values('broad_subjects', 'specific_fields')
        
        hierarchy = defaultdict(lambda: defaultdict(int))
        
        for paper in papers_with_subjects:
            broad = paper['broad_subjects'] or 'Unknown'
            specific = paper['specific_fields'] or 'General'
            
            # Take first broad subject if multiple
            if ';' in broad:
                broad = broad.split(';')[0].strip()
            
            # Take first specific field if multiple
            if specific and ';' in specific:
                specific = specific.split(';')[0].strip()
            
            hierarchy[broad][specific] += 1
        
        # Convert to sunburst format
        children = []
        for broad, specifics in hierarchy.items():
            specific_children = []
            for specific, count in specifics.items():
                specific_children.append({
                    'name': specific,
                    'value': count
                })
            
            children.append({
                'name': broad,
                'value': sum(specifics.values()),
                'children': sorted(specific_children, key=lambda x: x['value'], reverse=True)[:5]
            })
        
        return {
            'name': 'Subjects',
            'children': sorted(children, key=lambda x: x['value'], reverse=True)[:8]
        }
    
    @cached_function(timeout=1800, cache_alias='analytics', key_prefix='network_data')
    def _get_network_data(self):
        """Generate simplified network data for performance"""
        # Simplified network with top nodes only
        papers = RetractedPaper.objects.filter(
            citation_count__gt=10
        ).values('id', 'title', 'citation_count', 'journal')[:50]
        
        nodes = []
        for paper in papers:
            nodes.append({
                'id': paper['id'],
                'title': paper['title'][:50],
                'citations': paper['citation_count'],
                'journal': paper['journal'],
                'size': min(paper['citation_count'] / 2, 20)
            })
        
        # Simplified links (reduce complexity for performance)
        links = []
        citations = Citation.objects.filter(
            retracted_paper_id__in=[p['id'] for p in papers]
        ).select_related('citing_paper').values(
            'retracted_paper_id', 'citing_paper__journal'
        )[:200]
        
        for citation in citations:
            links.append({
                'source': citation['retracted_paper_id'],
                'target': citation['citing_paper__journal'] or 'Unknown',
                'value': 1
            })
        
        return {'nodes': nodes, 'links': links}
    
    @cached_function(timeout=1800, cache_alias='analytics', key_prefix='problematic_papers')
    def _get_problematic_papers(self):
        """Get problematic papers with caching and optimization"""
        return list(RetractedPaper.objects.filter(
            citation_count__gt=0
        ).annotate(
            post_retraction_citations=Count(
                'citation', filter=Q(citation__days_after_retraction__gt=0)
            )
        ).filter(
            post_retraction_citations__gt=5
        ).select_related().order_by('-post_retraction_citations')[:20])

# ============================================================================
# OPTIMIZED SEARCH VIEW
# ============================================================================

class OptimizedSearchView(ListView):
    """Optimized search with caching and efficient queries"""
    model = RetractedPaper
    template_name = 'papers/search.html'
    context_object_name = 'papers'
    paginate_by = 25
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        subject = self.request.GET.get('subject', '').strip()
        journal = self.request.GET.get('journal', '').strip()
        country = self.request.GET.get('country', '').strip()
        year_from = self.request.GET.get('year_from', '').strip()
        year_to = self.request.GET.get('year_to', '').strip()
        
        # Build cache key from search parameters
        cache_params = f"{query}:{subject}:{journal}:{country}:{year_from}:{year_to}"
        cache_key = f"search_results:{hash(cache_params)}"
        
        # Try cache first
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Build optimized queryset
        queryset = RetractedPaper.objects.select_related().prefetch_related(
            'citation_set'
        )
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(journal__icontains=query) |
                Q(subject__icontains=query)
            )
        
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        
        if journal:
            queryset = queryset.filter(journal__icontains=journal)
        
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        if year_from:
            try:
                queryset = queryset.filter(retraction_date__year__gte=int(year_from))
            except ValueError:
                pass
        
        if year_to:
            try:
                queryset = queryset.filter(retraction_date__year__lte=int(year_to))
            except ValueError:
                pass
        
        queryset = queryset.order_by('-retraction_date')
        
        # Cache results for 10 minutes
        cache.set(cache_key, queryset, 600)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter options (cached)
        context.update({
            'subjects': self._get_filter_options('subject'),
            'journals': self._get_filter_options('journal'),
            'countries': self._get_filter_options('country'),
            'search_query': self.request.GET.get('q', ''),
        })
        
        return context
    
    @cached_function(timeout=1800, cache_alias='default', key_prefix='filter_options')
    def _get_filter_options(self, field):
        """Get cached filter options"""
        return list(RetractedPaper.objects.exclude(
            **{f'{field}__isnull': True}
        ).exclude(
            **{f'{field}__exact': ''}
        ).values_list(field, flat=True).distinct().order_by(field)[:100])

# ============================================================================
# OPTIMIZED DETAIL VIEW
# ============================================================================

@method_decorator(cache_page(600), name='dispatch')  # 10 minute cache
class OptimizedPaperDetailView(DetailView):
    """Optimized paper detail view with efficient related queries"""
    model = RetractedPaper
    template_name = 'papers/paper_detail.html'
    context_object_name = 'paper'
    slug_field = 'record_id'
    slug_url_kwarg = 'record_id'
    
    def get_queryset(self):
        return RetractedPaper.objects.select_related().prefetch_related(
            Prefetch('citation_set',
                    queryset=Citation.objects.select_related('citing_paper').order_by('-citation_date')),
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paper = self.object
        
        # Optimized citation data
        citations = paper.citation_set.all()[:50]  # Limit for performance
        
        # Related papers (cached)
        related_papers = self._get_related_papers(paper)
        
        context.update({
            'citations': citations,
            'citation_count': paper.citation_count,
            'post_retraction_citations': citations.filter(days_after_retraction__gt=0).count(),
            'related_papers': related_papers,
        })
        
        return context
    
    @cached_function(timeout=1800, cache_alias='default', key_prefix='related_papers')
    def _get_related_papers(self, paper):
        """Get related papers with caching"""
        # Find papers with similar subjects or from same journal
        related = RetractedPaper.objects.exclude(
            id=paper.id
        ).filter(
            Q(journal=paper.journal) | 
            Q(subject__icontains=paper.subject.split(';')[0] if paper.subject else '')
        ).select_related().order_by('-citation_count')[:5]
        
        return list(related)

# ============================================================================
# API ENDPOINTS FOR REAL-TIME DATA
# ============================================================================

@require_http_methods(["GET"])
@cache_page(300)  # 5 minute cache
def analytics_api(request):
    """Optimized analytics API endpoint"""
    data_type = request.GET.get('type', 'overview')
    
    if data_type == 'overview':
        data = get_analytics_overview()
    elif data_type == 'trends':
        data = get_retraction_trends()
    elif data_type == 'citations':
        data = get_citation_analysis()
    elif data_type == 'subjects':
        data = get_subject_analysis()
    elif data_type == 'geographic':
        data = get_geographic_analysis()
    else:
        data = {'error': 'Invalid data type'}
    
    return JsonResponse(data, safe=False)

@require_http_methods(["POST"])
@csrf_exempt
def warm_cache(request):
    """Enhanced endpoint to warm up caches with proper error handling"""
    try:
        # Parse JSON body
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                cache_type = data.get('type', 'all')
            else:
                cache_type = request.POST.get('type', 'all')
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'error': {
                    'code': 'INVALID_JSON',
                    'message': 'Invalid JSON in request body'
                }
            }, status=400)
        
        # Validate cache type
        valid_cache_types = ['all', 'analytics']
        if cache_type not in valid_cache_types:
            return JsonResponse({
                'status': 'error',
                'error': {
                    'code': 'INVALID_CACHE_TYPE',
                    'message': f'Invalid cache type. Must be one of: {", ".join(valid_cache_types)}'
                }
            }, status=400)
        
        # Warm up caches
        if cache_type == 'analytics':
            # Warm analytics-specific caches
            from .utils.cache_utils import get_analytics_overview, get_retraction_trends, get_citation_analysis
            
            get_analytics_overview()
            get_retraction_trends()
            get_citation_analysis()
            
            message = 'Analytics cache warmed successfully'
        else:
            # Warm all caches
            from .utils.cache_utils import get_analytics_overview, get_retraction_trends, get_citation_analysis, get_subject_analysis
            
            get_analytics_overview()
            get_retraction_trends()  
            get_citation_analysis()
            get_subject_analysis()
            
            message = 'All caches warmed successfully'
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'cache_type': cache_type,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error while warming cache'
            }
        }, status=500) 