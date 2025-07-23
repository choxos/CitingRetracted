from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Case, When, IntegerField, F, Max
from django.db import models
from django.conf import settings
from django.views.generic import ListView, DetailView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import RetractedPaper, CitingPaper, Citation, DataImportLog
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.generic import View


class HomeView(ListView):
    """Homepage with search and recent retractions"""
    model = RetractedPaper
    template_name = 'papers/home.html'
    context_object_name = 'recent_papers'
    paginate_by = 10
    
    def get_queryset(self):
        return RetractedPaper.objects.filter(
            retraction_date__isnull=False
        ).order_by('-retraction_date')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get summary statistics
        total_retracted = RetractedPaper.objects.count()
        context['total_retracted'] = total_retracted
        context['total_citations'] = Citation.objects.count()
        context['current_year'] = timezone.now().year
        context['recent_retractions'] = RetractedPaper.objects.filter(
            retraction_date__gte=timezone.now().date() - timedelta(days=365)
        ).count()
        
        # Post-retraction citation stats for homepage
        context['post_retraction_citations'] = Citation.objects.filter(
            days_after_retraction__gt=0
        ).count()
        
        # Sidebar statistics
        # Top reasons  
        context['top_reasons'] = RetractedPaper.objects.exclude(
            Q(reason__isnull=True) | Q(reason__exact='')
        ).values('reason').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top publishers
        context['top_publishers'] = RetractedPaper.objects.exclude(
            Q(publisher__isnull=True) | Q(publisher__exact='')
        ).values('publisher').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top countries
        context['top_countries'] = RetractedPaper.objects.exclude(
            Q(country__isnull=True) | Q(country__exact='')
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top institutions
        context['top_institutions'] = RetractedPaper.objects.exclude(
            Q(institution__isnull=True) | Q(institution__exact='')
        ).values('institution').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top authors (extract from JSON authors field)
        context['top_authors'] = self._get_top_authors()
        
        # Top subjects
        context['top_subjects'] = RetractedPaper.objects.exclude(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).values('subject').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Get top journals with retractions  
        context['top_journals'] = RetractedPaper.objects.values('journal').annotate(
            count=Count('id')
        ).exclude(journal__isnull=True).exclude(journal__exact='').order_by('-count')[:5]
        
        # Latest citing papers (papers that recently cited retracted papers)
        context['latest_citing_papers'] = Citation.objects.select_related(
            'citing_paper', 'retracted_paper'
        ).filter(
            citing_paper__publication_date__isnull=False
        ).order_by('-citing_paper__publication_date')[:10]
        
        return context
    
    def _get_top_authors(self):
        """Extract and count top authors from semicolon-separated authors field"""
        from collections import Counter
        
        author_counts = Counter()
        
        # Get papers with authors data
        papers_with_authors = RetractedPaper.objects.exclude(
            Q(author__isnull=True) | Q(author__exact='')
        ).values_list('author', flat=True)
        
        for authors_string in papers_with_authors:
            if authors_string:
                # Split by semicolon and clean up each author name
                authors = [author.strip() for author in authors_string.split(';')]
                for author in authors:
                    if author and len(author) > 2:  # Filter out very short names
                        author_counts[author] += 1
        
        # Return top 5 authors as list of dicts for template compatibility
        return [{'author': author, 'count': count} 
                for author, count in author_counts.most_common(5)]


class SearchView(ListView):
    """Search functionality for retracted papers"""
    model = RetractedPaper
    template_name = 'papers/search.html'
    context_object_name = 'papers'
    paginate_by = settings.PAPERS_PER_PAGE
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        journal = self.request.GET.get('journal', '').strip()
        year_from = self.request.GET.get('year_from', '').strip()
        year_to = self.request.GET.get('year_to', '').strip()
        subject = self.request.GET.get('subject', '').strip()
        reason = self.request.GET.get('reason', '').strip()
        country = self.request.GET.get('country', '').strip()
        institution = self.request.GET.get('institution', '').strip()
        author = self.request.GET.get('author', '').strip()
        publisher = self.request.GET.get('publisher', '').strip()
        
        queryset = RetractedPaper.objects.all()
        
        if query:
            # Use full-text search if available, otherwise fall back to icontains
            try:
                # PostgreSQL full-text search
                search_vector = SearchVector('title', 'author', 'reason', 'abstract')
                search_query = SearchQuery(query)
                queryset = queryset.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query)
                ).filter(search=search_query).order_by('-rank', '-retraction_date')
            except:
                # Fallback for SQLite and other databases
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(author__icontains=query) |
                    Q(reason__icontains=query) |
                    Q(journal__icontains=query) |
                    Q(record_id__icontains=query)
                ).order_by('-retraction_date')
        
        # Apply filters
        if journal:
            queryset = queryset.filter(journal__icontains=journal)
        
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        
        if reason:
            queryset = queryset.filter(reason__icontains=reason)
        
        if country:
            # Handle semicolon-separated countries
            queryset = queryset.filter(
                Q(country__icontains=f';{country};') |  # Middle of list
                Q(country__startswith=f'{country};') |  # Start of list
                Q(country__endswith=f';{country}') |    # End of list  
                Q(country__exact=country)               # Single country
            )
        
        if institution:
            queryset = queryset.filter(institution__icontains=institution)
        
        if author:
            queryset = queryset.filter(author__icontains=author)
        
        if publisher:
            queryset = queryset.filter(publisher__icontains=publisher)
        
        if year_from:
            try:
                year_from = int(year_from)
                queryset = queryset.filter(retraction_date__year__gte=year_from)
            except ValueError:
                pass
        
        if year_to:
            try:
                year_to = int(year_to)
                queryset = queryset.filter(retraction_date__year__lte=year_to)
            except ValueError:
                pass
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Current filter values for preserving form state
        context['search_query'] = self.request.GET.get('q', '')
        context['journal_filter'] = self.request.GET.get('journal', '')
        context['year_from'] = self.request.GET.get('year_from', '')
        context['year_to'] = self.request.GET.get('year_to', '')
        context['subject_filter'] = self.request.GET.get('subject', '')
        context['reason_filter'] = self.request.GET.get('reason', '')
        context['country_filter'] = self.request.GET.get('country', '')
        context['institution_filter'] = self.request.GET.get('institution', '')
        context['author_filter'] = self.request.GET.get('author', '')
        context['publisher_filter'] = self.request.GET.get('publisher', '')
        
        # Get dropdown options for select fields
        context['subjects'] = RetractedPaper.objects.values_list(
            'subject', flat=True
        ).distinct().exclude(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).order_by('subject')  # Show all subjects, no limit
        
        context['reasons'] = RetractedPaper.objects.values_list(
            'reason', flat=True
        ).distinct().exclude(
            Q(reason__isnull=True) | Q(reason__exact='')
        ).order_by('reason')  # Show all reasons, no limit
        
        # Get individual countries from semicolon-separated strings
        country_strings = RetractedPaper.objects.values_list(
            'country', flat=True
        ).distinct().exclude(
            Q(country__isnull=True) | Q(country__exact='')
        )
        
        # Extract individual countries
        all_countries = set()
        for country_string in country_strings:
            if country_string:
                countries = [country.strip() for country in country_string.split(';')]
                all_countries.update(countries)
        
        # Remove invalid entries and sort
        invalid_entries = {'', 'Unknown', 'unknown', 'N/A', 'n/a', 'None', 'null'}
        clean_countries = sorted(list(all_countries - invalid_entries))
        context['countries'] = clean_countries  # Show all countries, no limit
        
        # Institution is now a text input, so no need for dropdown options
        
        context['publishers'] = RetractedPaper.objects.values_list(
            'publisher', flat=True
        ).distinct().exclude(
            Q(publisher__isnull=True) | Q(publisher__exact='')
        ).order_by('publisher')  # Show all publishers, no limit
        
        return context


class PaperDetailView(DetailView):
    """Detail view for a retracted paper"""
    model = RetractedPaper
    template_name = 'papers/paper_detail.html'
    context_object_name = 'paper'
    slug_field = 'record_id'
    slug_url_kwarg = 'record_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paper = self.object
        
        # Get citations for this paper
        citations = Citation.objects.filter(retracted_paper=paper).select_related('citing_paper').order_by('-citing_paper__publication_date')
        
        # Paginate citations
        paginator = Paginator(citations, settings.CITATIONS_PER_PAGE)
        page_number = self.request.GET.get('page')
        context['citations'] = paginator.get_page(page_number)
        
        # Enhanced citation analytics with post-retraction focus
        total_citations = citations.count()
        post_retraction = citations.filter(days_after_retraction__gt=0)
        pre_retraction = citations.filter(days_after_retraction__lt=0)
        same_day = citations.filter(days_after_retraction=0)
        
        context['citation_stats'] = {
            'total_citations': total_citations,
            'post_retraction_citations': post_retraction.count(),
            'pre_retraction_citations': pre_retraction.count(),
            'same_day_citations': same_day.count(),
            'post_retraction_percentage': (post_retraction.count() / max(total_citations, 1)) * 100,
        }
        
        # Post-retraction citation timeline analysis
        if post_retraction.exists():
            context['post_retraction_stats'] = {
                'within_30_days': post_retraction.filter(days_after_retraction__lte=30).count(),
                'within_1_year': post_retraction.filter(days_after_retraction__lte=365).count(),
                'within_2_years': post_retraction.filter(days_after_retraction__lte=730).count(),
                'after_2_years': post_retraction.filter(days_after_retraction__gt=730).count(),
                'latest_citation_days': post_retraction.aggregate(
                    max_days=models.Max('days_after_retraction')
                )['max_days'],
                'average_days_after': post_retraction.aggregate(
                    avg_days=models.Avg('days_after_retraction')
                )['avg_days'],
            }
        
        # Citations by year with post-retraction highlighting
        citation_years = citations.values('citing_paper__publication_year').annotate(
            count=Count('id'),
            post_retraction_count=Count(
                Case(When(days_after_retraction__gt=0, then=1),
                     output_field=IntegerField())
            )
        ).order_by('citing_paper__publication_year')
        context['citation_years'] = list(citation_years)
        
        # Recent post-retraction citations (most concerning)
        context['recent_post_retraction'] = post_retraction.order_by('days_after_retraction')[:5]
        
        # Related papers (same journal or subject)
        related_papers = RetractedPaper.objects.filter(
            Q(journal=paper.journal) | Q(subject=paper.subject)
        ).exclude(id=paper.id)[:5]
        context['related_papers'] = related_papers
        
        return context


class AnalyticsView(ListView):
    """Enhanced analytics dashboard with post-retraction focus"""
    template_name = 'papers/analytics.html'
    model = RetractedPaper
    context_object_name = 'papers'
    
    def get_queryset(self):
        return RetractedPaper.objects.none()  # We're not displaying papers directly
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics
        total_papers = RetractedPaper.objects.count()
        total_citations = Citation.objects.count()
        post_retraction_citations = Citation.objects.filter(days_after_retraction__gt=0).count()
        
        context['stats'] = {
            'total_papers': total_papers,
            'total_citations': total_citations,
            'post_retraction_citations': post_retraction_citations,
            'post_retraction_percentage': (post_retraction_citations / max(total_citations, 1)) * 100,
            'avg_citations_per_paper': total_citations / max(total_papers, 1),
            'recent_retractions': RetractedPaper.objects.filter(
                retraction_date__gte=timezone.now().date() - timedelta(days=365)
            ).count()
        }
        
        # Post-retraction citation timeline analysis
        post_retraction_qs = Citation.objects.filter(days_after_retraction__gt=0)
        context['post_retraction_timeline'] = {
            'within_30_days': post_retraction_qs.filter(days_after_retraction__lte=30).count(),
            'within_6_months': post_retraction_qs.filter(days_after_retraction__lte=180).count(),
            'within_1_year': post_retraction_qs.filter(days_after_retraction__lte=365).count(),
            'within_2_years': post_retraction_qs.filter(days_after_retraction__lte=730).count(),
            'after_2_years': post_retraction_qs.filter(days_after_retraction__gt=730).count(),
        }
        
        # Retractions by year (database-agnostic)
        from django.db.models.functions import TruncYear
        retraction_years = RetractedPaper.objects.filter(
            retraction_date__isnull=False
        ).annotate(
            year=TruncYear('retraction_date')
        ).values('year').annotate(
            count=Count('id')
        ).order_by('year')
        
        # Convert to format expected by JavaScript charts
        retraction_years_data = []
        for item in retraction_years:
            retraction_years_data.append({
                'year': item['year'].year if item['year'] else 'Unknown',
                'count': item['count']
            })
        context['retraction_years'] = retraction_years_data
        
        # Top journals with post-retraction citation issues
        context['top_journals'] = RetractedPaper.objects.values('journal').annotate(
            retraction_count=Count('id'),
            total_citations=Count('citations'),
            post_retraction_citations=Count(
                'citations',
                filter=Q(citations__days_after_retraction__gt=0)
            )
        ).exclude(journal__isnull=True).order_by('-post_retraction_citations')[:10]
        
        # Top subjects with retraction issues
        context['top_subjects'] = RetractedPaper.objects.values('subject').annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations',
                filter=Q(citations__days_after_retraction__gt=0)
            )
        ).exclude(subject__isnull=True).order_by('-post_retraction_citations')[:10]
        
        # Citation patterns - enhanced with timeline
        pre_retraction_citations = Citation.objects.filter(days_after_retraction__lt=0).count()
        same_day_citations = Citation.objects.filter(days_after_retraction=0).count()
        
        context['citation_patterns'] = {
            'post_retraction': post_retraction_citations,
            'pre_retraction': pre_retraction_citations,
            'same_day': same_day_citations,
            'post_retraction_percentage': (post_retraction_citations / max(total_citations, 1)) * 100
        }
        
        # Papers with most post-retraction citations (most problematic)
        context['most_cited_post_retraction'] = RetractedPaper.objects.annotate(
            post_retraction_count=Count(
                'citations',
                filter=Q(citations__days_after_retraction__gt=0)
            )
        ).filter(post_retraction_count__gt=0).order_by('-post_retraction_count')[:10]
        
        # Recent activity
        context['recent_imports'] = DataImportLog.objects.order_by('-start_time')[:5]
        
        # Post-retraction citation trends by month (for chart)
        from django.db.models.functions import TruncMonth
        monthly_post_retraction = Citation.objects.filter(
            days_after_retraction__gt=0,
            created_at__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Convert to format expected by JavaScript charts
        monthly_data = []
        for item in monthly_post_retraction:
            monthly_data.append({
                'month': item['month'].strftime('%Y-%m') if item['month'] else 'Unknown',
                'count': item['count']
            })
        context['monthly_post_retraction'] = monthly_data
        
        # Advanced analytics for enhanced visualizations
        context.update(self._get_advanced_analytics())
        
        return context
    
    def _get_advanced_analytics(self):
        """Generate advanced analytics data for enhanced visualizations."""
        from django.db.models.functions import TruncMonth, TruncYear, Extract
        from django.db.models import F, Avg, Max, Min, StdDev
        import calendar
        
        advanced_data = {}
        
        # 1. Country-based analytics
        country_analytics = RetractedPaper.objects.exclude(
            country__isnull=True
        ).exclude(country__exact='').values('country').annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            open_access_count=Count('id', filter=Q(is_open_access=True)),
            avg_citations=Avg('citation_count')
        ).order_by('-retraction_count')[:15]
        
        advanced_data['country_analytics'] = [
            {
                'country': item['country'],
                'retraction_count': item['retraction_count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'open_access_count': item['open_access_count'],
                'open_access_percentage': (item['open_access_count'] / max(item['retraction_count'], 1)) * 100,
                'avg_citations': round(item['avg_citations'] or 0, 1)
            }
            for item in country_analytics
        ]
        
        # 2. Article type analytics
        article_type_analytics = RetractedPaper.objects.exclude(
            article_type__isnull=True
        ).exclude(article_type__exact='').values('article_type').annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            open_access_count=Count('id', filter=Q(is_open_access=True))
        ).order_by('-count')[:10]
        
        advanced_data['article_type_analytics'] = [
            {
                'type': item['article_type'],
                'count': item['count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'open_access_count': item['open_access_count'],
                'citation_rate': (item['post_retraction_citations'] / max(item['count'], 1)) * 100
            }
            for item in article_type_analytics
        ]
        
        # 3. Publisher analytics
        publisher_analytics = RetractedPaper.objects.exclude(
            publisher__isnull=True
        ).exclude(publisher__exact='').values('publisher').annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            open_access_count=Count('id', filter=Q(is_open_access=True))
        ).order_by('-retraction_count')[:10]
        
        advanced_data['publisher_analytics'] = [
            {
                'publisher': item['publisher'],
                'retraction_count': item['retraction_count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'open_access_count': item['open_access_count'],
                'impact_score': item['retraction_count'] * (item['post_retraction_citations'] or 0)
            }
            for item in publisher_analytics
        ]
        
        # 4. Open Access vs Paywalled analysis
        access_analytics = {
            'open_access': {
                'count': RetractedPaper.objects.filter(is_open_access=True).count(),
                'post_retraction_citations': Citation.objects.filter(
                    retracted_paper__is_open_access=True,
                    days_after_retraction__gt=0
                ).count()
            },
            'paywalled': {
                'count': RetractedPaper.objects.filter(paywalled=True).count(),
                'post_retraction_citations': Citation.objects.filter(
                    retracted_paper__paywalled=True,
                    days_after_retraction__gt=0
                ).count()
            },
            'unknown': {
                'count': RetractedPaper.objects.filter(
                    is_open_access=False, paywalled=False
                ).count(),
                'post_retraction_citations': Citation.objects.filter(
                    retracted_paper__is_open_access=False,
                    retracted_paper__paywalled=False,
                    days_after_retraction__gt=0
                ).count()
            }
        }
        
        # Calculate percentages
        total_papers = RetractedPaper.objects.count()
        for access_type in access_analytics:
            count = access_analytics[access_type]['count']
            access_analytics[access_type]['percentage'] = (count / max(total_papers, 1)) * 100
            
            citations = access_analytics[access_type]['post_retraction_citations']
            access_analytics[access_type]['citations_per_paper'] = citations / max(count, 1)
        
        advanced_data['access_analytics'] = access_analytics
        
        # 5. Top institutions with retraction issues
        institution_analytics = RetractedPaper.objects.exclude(
            institution__isnull=True
        ).exclude(institution__exact='').values('institution').annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            unique_journals=Count('journal', distinct=True)
        ).order_by('-retraction_count')[:15]
        
        advanced_data['institution_analytics'] = [
            {
                'institution': item['institution'][:100] + '...' if len(item['institution']) > 100 else item['institution'],
                'retraction_count': item['retraction_count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'unique_journals': item['unique_journals'],
                'problem_score': item['retraction_count'] + (item['post_retraction_citations'] * 2)
            }
            for item in institution_analytics
        ]
        
        # 6. Citation timeline heatmap data (by month and days after retraction)
        citation_heatmap = []
        for month in range(1, 13):
            month_data = []
            buckets = [30, 90, 180, 365, 730, 9999]
            prev_bucket = 0
            
            for i, bucket in enumerate(buckets):
                if bucket == 9999:
                    count = Citation.objects.filter(
                        retracted_paper__retraction_date__month=month,
                        days_after_retraction__gt=730
                    ).count()
                else:
                    count = Citation.objects.filter(
                        retracted_paper__retraction_date__month=month,
                        days_after_retraction__gt=prev_bucket,
                        days_after_retraction__lte=bucket
                    ).count()
                    prev_bucket = bucket
                month_data.append(count)
            citation_heatmap.append({
                'month': calendar.month_name[month],
                'data': month_data
            })
        advanced_data['citation_heatmap'] = citation_heatmap
        
        # 7. Journal impact analysis with bubble chart data
        journal_impact = RetractedPaper.objects.values('journal').annotate(
            retraction_count=Count('id'),
            avg_citations=Avg('citation_count'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).filter(
            retraction_count__gte=2,  # At least 2 retractions
            journal__isnull=False
        ).order_by('-post_retraction_citations')[:20]
        
        advanced_data['journal_bubble_data'] = [
            {
                'journal': item['journal'][:30] + '...' if len(item['journal']) > 30 else item['journal'],
                'x': item['retraction_count'],
                'y': item['post_retraction_citations'] or 0,
                'size': max(5, (item['avg_citations'] or 0) / 10),
                'impact_score': (item['post_retraction_citations'] or 0) * item['retraction_count'],
                'full_name': item['journal']
            }
            for item in journal_impact
        ]
        
        # 8. Subject area distribution with interactive donut
        subject_distribution = RetractedPaper.objects.exclude(
            subject__isnull=True
        ).exclude(subject__exact='').values('subject').annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            open_access_count=Count('id', filter=Q(is_open_access=True))
        ).order_by('-count')[:15]
        
        advanced_data['subject_donut_data'] = [
            {
                'subject': item['subject'],
                'count': item['count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'open_access_count': item['open_access_count'],
                'open_access_rate': (item['open_access_count'] / max(item['count'], 1)) * 100
            }
            for item in subject_distribution
        ]
        
        # 9. Time-to-citation analysis (violin plot data)
        citation_timing = Citation.objects.filter(
            days_after_retraction__gte=0,
            days_after_retraction__lte=1095  # 3 years
        ).values('days_after_retraction').annotate(
            count=Count('id')
        ).order_by('days_after_retraction')
        
        advanced_data['citation_timing_distribution'] = [
            {
                'days': item['days_after_retraction'],
                'count': item['count']
            }
            for item in citation_timing
        ]
        
        # 10. Comparative timeline (before vs after retraction)
        retraction_comparison = []
        for years_back in range(0, 6):  # 6 years of data
            year_start = timezone.now().date() - timedelta(days=365 * (years_back + 1))
            year_end = timezone.now().date() - timedelta(days=365 * years_back)
            
            pre_retraction = Citation.objects.filter(
                days_after_retraction__lt=0,
                created_at__date__gte=year_start,
                created_at__date__lt=year_end
            ).count()
            
            post_retraction = Citation.objects.filter(
                days_after_retraction__gt=0,
                created_at__date__gte=year_start,
                created_at__date__lt=year_end
            ).count()
            
            retraction_comparison.append({
                'year': year_end.year,
                'pre_retraction': pre_retraction,
                'post_retraction': post_retraction
            })
        
        advanced_data['retraction_comparison'] = list(reversed(retraction_comparison))
        
        # 11. Top papers analysis with detailed metrics
        top_problematic_papers = RetractedPaper.objects.annotate(
            post_retraction_count=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            total_citation_count=Count('citations')
        ).filter(
            post_retraction_count__gt=0,
            total_citation_count__gt=0,
            record_id__isnull=False
        ).exclude(record_id__exact='').order_by('-post_retraction_count')[:20]
        
        advanced_data['problematic_papers_detailed'] = []
        for paper in top_problematic_papers:
            citation_rate = 0
            if paper.total_citation_count > 0:
                citation_rate = (paper.post_retraction_count / paper.total_citation_count) * 100
            
            days_since_retraction = 0
            if paper.retraction_date:
                days_since_retraction = (timezone.now().date() - paper.retraction_date).days
            
            advanced_data['problematic_papers_detailed'].append({
                'record_id': paper.record_id,
                'title': paper.title[:60] + '...' if len(paper.title) > 60 else paper.title,
                'journal': paper.journal,
                'country': paper.country,
                'institution': paper.institution[:50] + '...' if paper.institution and len(paper.institution) > 50 else paper.institution,
                'retraction_date': paper.retraction_date.strftime('%Y-%m-%d') if paper.retraction_date else None,
                'post_retraction_citations': paper.post_retraction_count,
                'total_citations': paper.total_citation_count,
                'citation_rate': citation_rate,
                'days_since_retraction': days_since_retraction,
                'access_status': paper.access_status,
                'reason': paper.reason[:100] + '...' if paper.reason and len(paper.reason) > 100 else paper.reason,
                'original_paper_url': paper.original_paper_url,
                'pubmed_url': paper.original_paper_pubmed_url
            })
        
        # 12. Network analysis data (simplified - journals and subject connections)
        network_nodes = []
        network_links = []
        
        # Add journal nodes
        top_journals = RetractedPaper.objects.values('journal').annotate(
            count=Count('id')
        ).filter(journal__isnull=False).order_by('-count')[:10]
        
        for i, journal in enumerate(top_journals):
            network_nodes.append({
                'id': f"journal_{i}",
                'name': journal['journal'][:20] + '...' if len(journal['journal']) > 20 else journal['journal'],
                'type': 'journal',
                'size': journal['count'],
                'full_name': journal['journal']
            })
        
        # Add subject nodes and links
        top_subjects = RetractedPaper.objects.values('subject').annotate(
            count=Count('id')
        ).filter(subject__isnull=False).order_by('-count')[:8]
        
        for i, subject in enumerate(top_subjects):
            network_nodes.append({
                'id': f"subject_{i}",
                'name': subject['subject'][:15] + '...' if len(subject['subject']) > 15 else subject['subject'],
                'type': 'subject',
                'size': subject['count'],
                'full_name': subject['subject']
            })
        
        advanced_data['network_data'] = {
            'nodes': network_nodes,
            'links': network_links
        }
        
        return advanced_data


class PostRetractionAnalyticsAPIView(View):
    """API endpoint for post-retraction citation analytics."""
    
    def get(self, request):
        # Get filter parameters
        time_filter = request.GET.get('time_filter', 'all')
        journal_filter = request.GET.get('journal', '')
        subject_filter = request.GET.get('subject', '')
        
        # Base queryset with filters
        citations_qs = Citation.objects.filter(days_after_retraction__gt=0)
        
        if time_filter != 'all':
            cutoff_days = {
                '1y': 365,
                '3y': 1095,
                '5y': 1825
            }.get(time_filter, 365)
            cutoff_date = timezone.now().date() - timedelta(days=cutoff_days)
            citations_qs = citations_qs.filter(created_at__date__gte=cutoff_date)
        
        if journal_filter:
            citations_qs = citations_qs.filter(retraction_paper__journal__icontains=journal_filter)
            
        if subject_filter:
            citations_qs = citations_qs.filter(retraction_paper__subject__icontains=subject_filter)
        
        # Calculate metrics
        total_post_retraction = citations_qs.count()
        
        # Time distribution
        time_distribution = {
            'within_30_days': citations_qs.filter(days_after_retraction__lte=30).count(),
            'within_6_months': citations_qs.filter(days_after_retraction__lte=180).count(),
            'within_1_year': citations_qs.filter(days_after_retraction__lte=365).count(),
            'within_2_years': citations_qs.filter(days_after_retraction__lte=730).count(),
            'after_2_years': citations_qs.filter(days_after_retraction__gt=730).count(),
        }
        
        # Monthly trend data
        from django.db.models.functions import TruncMonth
        monthly_trend = citations_qs.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        monthly_data = [
            {
                'month': item['month'].strftime('%Y-%m') if item['month'] else 'Unknown',
                'count': item['count']
            }
            for item in monthly_trend
        ]
        
        data = {
            'total_post_retraction': total_post_retraction,
            'time_distribution': time_distribution,
            'monthly_trend': monthly_data,
            'filters_applied': {
                'time_filter': time_filter,
                'journal_filter': journal_filter,
                'subject_filter': subject_filter
            }
        }
        
        return JsonResponse(data)


class AnalyticsDataAPIView(View):
    """API endpoint for comprehensive analytics data with filtering."""
    
    def get(self, request):
        # Get filter parameters
        chart_type = request.GET.get('chart', 'overview')
        time_filter = request.GET.get('time_filter', 'all')
        
        if chart_type == 'retractions_timeline':
            data = self._get_retractions_timeline_data(time_filter)
        elif chart_type == 'citation_heatmap':
            data = self._get_citation_heatmap_data(time_filter)
        elif chart_type == 'journal_bubble':
            data = self._get_journal_bubble_data(time_filter)
        elif chart_type == 'subject_distribution':
            data = self._get_subject_distribution_data(time_filter)
        else:
            data = {'error': 'Unknown chart type'}
            
        return JsonResponse(data)
    
    def _get_retractions_timeline_data(self, time_filter):
        """Get retraction timeline data with time filtering."""
        from django.db.models.functions import TruncYear
        
        papers_qs = RetractedPaper.objects.filter(retraction_date__isnull=False)
        
        if time_filter != 'all':
            years_back = {
                '5y': 5,
                '3y': 3,
                '1y': 1
            }.get(time_filter, 5)
            cutoff_date = timezone.now().date() - timedelta(days=365 * years_back)
            papers_qs = papers_qs.filter(retraction_date__gte=cutoff_date)
        
        timeline_data = papers_qs.annotate(
            year=TruncYear('retraction_date')
        ).values('year').annotate(
            count=Count('id')
        ).order_by('year')
        
        return {
            'labels': [item['year'].year for item in timeline_data],
            'data': [item['count'] for item in timeline_data]
        }
    
    def _get_citation_heatmap_data(self, time_filter):
        """Get citation heatmap data."""
        import calendar
        
        heatmap_data = []
        for month in range(1, 13):
            month_data = []
            for bucket in [30, 90, 180, 365, 730, 9999]:
                if bucket == 9999:
                    count = Citation.objects.filter(
                        retraction_paper__retraction_date__month=month,
                        days_after_retraction__gt=730
                    ).count()
                else:
                    prev_bucket = 0 if bucket == 30 else [30, 90, 180, 365, 730][month_data.__len__()]
                    count = Citation.objects.filter(
                        retraction_paper__retraction_date__month=month,
                        days_after_retraction__gt=prev_bucket,
                        days_after_retraction__lte=bucket
                    ).count()
                month_data.append(count)
            heatmap_data.append({
                'month': calendar.month_name[month],
                'data': month_data
            })
        
        return {
            'months': [item['month'] for item in heatmap_data],
            'buckets': ['0-30 days', '30-90 days', '90-180 days', '180-365 days', '1-2 years', '2+ years'],
            'data': [item['data'] for item in heatmap_data]
        }
    
    def _get_journal_bubble_data(self, time_filter):
        """Get journal bubble chart data."""
        journals = RetractedPaper.objects.values('journal').annotate(
            retraction_count=Count('id'),
            avg_citations=Avg('total_citations'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).filter(
            retraction_count__gte=2,
            journal__isnull=False
        ).order_by('-post_retraction_citations')[:15]
        
        return {
            'journals': [
                {
                    'name': item['journal'][:30] + '...' if len(item['journal']) > 30 else item['journal'],
                    'x': item['retraction_count'],
                    'y': item['post_retraction_citations'] or 0,
                    'size': max(5, (item['avg_citations'] or 0) / 5),
                    'full_name': item['journal']
                }
                for item in journals
            ]
        }
    
    def _get_subject_distribution_data(self, time_filter):
        """Get subject distribution data."""
        subjects = RetractedPaper.objects.values('subject').annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).filter(subject__isnull=False).order_by('-count')[:12]
        
        return {
            'labels': [item['subject'] for item in subjects],
            'data': [item['count'] for item in subjects],
            'post_retraction_data': [item['post_retraction_citations'] for item in subjects]
        }


def search_autocomplete(request):
    """AJAX endpoint for search autocomplete"""
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return JsonResponse({'suggestions': []})
    
    # Search in titles and authors
    papers = RetractedPaper.objects.filter(
        Q(title__icontains=query) | Q(author__icontains=query)
    )[:10]
    
    suggestions = []
    for paper in papers:
        suggestions.append({
            'title': paper.title,
            'author': paper.author or '',
            'journal': paper.journal or '',
            'record_id': paper.record_id,
            'url': paper.get_absolute_url(),
            'post_retraction_citations': paper.citations.filter(days_after_retraction__gt=0).count()
        })
    
    return JsonResponse({'suggestions': suggestions})


def paper_citations_json(request, record_id):
    """Enhanced AJAX endpoint for paper citations data with post-retraction analysis"""
    paper = get_object_or_404(RetractedPaper, record_id=record_id)
    
    citations = Citation.objects.filter(retracted_paper=paper).select_related('citing_paper')
    
    # Group by year with post-retraction breakdown
    citations_by_year = {}
    post_retraction_by_year = {}
    
    for citation in citations:
        year = citation.citing_paper.publication_year or 'Unknown'
        if year not in citations_by_year:
            citations_by_year[year] = 0
            post_retraction_by_year[year] = 0
        
        citations_by_year[year] += 1
        if citation.days_after_retraction and citation.days_after_retraction > 0:
            post_retraction_by_year[year] += 1
    
    # Timeline data for post-retraction analysis
    timeline_data = []
    post_retraction_timeline = []
    
    for citation in citations:
        citation_data = {
            'days_after': citation.days_after_retraction,
            'citing_paper': citation.citing_paper.title,
            'publication_date': citation.citing_paper.publication_date.isoformat() if citation.citing_paper.publication_date else None,
            'is_post_retraction': citation.days_after_retraction and citation.days_after_retraction > 0
        }
        timeline_data.append(citation_data)
        
        if citation.days_after_retraction and citation.days_after_retraction > 0:
            post_retraction_timeline.append(citation_data)
    
    # Post-retraction statistics
    post_retraction_stats = {
        'within_30_days': len([c for c in post_retraction_timeline if c['days_after'] <= 30]),
        'within_1_year': len([c for c in post_retraction_timeline if c['days_after'] <= 365]),
        'within_2_years': len([c for c in post_retraction_timeline if c['days_after'] <= 730]),
        'after_2_years': len([c for c in post_retraction_timeline if c['days_after'] > 730]),
    }
    
    return JsonResponse({
        'citations_by_year': citations_by_year,
        'post_retraction_by_year': post_retraction_by_year,
        'timeline_data': timeline_data,
        'post_retraction_timeline': post_retraction_timeline,
        'post_retraction_stats': post_retraction_stats,
        'total_citations': citations.count(),
        'post_retraction_count': len(post_retraction_timeline)
    })


def post_retraction_analytics_json(request):
    """AJAX endpoint for post-retraction analytics charts"""
    
    # Timeline distribution
    timeline_stats = Citation.objects.filter(
        days_after_retraction__gt=0
    ).aggregate(
        within_30_days=Count(Case(When(days_after_retraction__lte=30, then=1))),
        within_6_months=Count(Case(When(days_after_retraction__lte=180, then=1))),
        within_1_year=Count(Case(When(days_after_retraction__lte=365, then=1))),
        within_2_years=Count(Case(When(days_after_retraction__lte=730, then=1))),
        after_2_years=Count(Case(When(days_after_retraction__gt=730, then=1))),
    )
    
    # Top journals with post-retraction citations
    top_journals = list(RetractedPaper.objects.values('journal').annotate(
        post_retraction_citations=Count(
            'citations',
            filter=Q(citations__days_after_retraction__gt=0)
        )
    ).exclude(journal__isnull=True).filter(
        post_retraction_citations__gt=0
    ).order_by('-post_retraction_citations')[:10])
    
    return JsonResponse({
        'timeline_stats': timeline_stats,
        'top_journals': top_journals
    })


def export_data(request):
    """Enhanced export functionality with post-retraction data"""
    papers = RetractedPaper.objects.all()
    
    data = []
    for paper in papers:
        post_retraction_count = paper.citations.filter(days_after_retraction__gt=0).count()
        data.append({
            'record_id': paper.record_id,
            'title': paper.title,
            'author': paper.author,
            'journal': paper.journal,
            'retraction_date': paper.retraction_date.isoformat() if paper.retraction_date else None,
            'total_citations': paper.citation_count,
            'post_retraction_citations': post_retraction_count,
            'post_retraction_percentage': (post_retraction_count / max(paper.citation_count, 1)) * 100,
            'reason': paper.reason
        })
    
    return JsonResponse({'papers': data})
