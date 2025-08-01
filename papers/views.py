from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Case, When, IntegerField, F, Max, Sum
from django.db import models
from django.conf import settings
from django.views.generic import ListView, DetailView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import RetractedPaper, CitingPaper, Citation, DataImportLog
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.generic import View
from django.views.decorators.cache import cache_page
import calendar


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
        
        # Get summary statistics in one query
        stats = RetractedPaper.objects.aggregate(
            total_retracted=Count('id'),
            recent_retractions=Count('id', filter=Q(
                retraction_date__gte=timezone.now().date() - timedelta(days=365)
            )),
        )
        context.update(stats)
        context['current_year'] = timezone.now().year
        context['current_date'] = timezone.now().date()
        
        # Get citation stats efficiently
        citation_stats = Citation.objects.aggregate(
            total_citations=Count('id'),
            post_retraction_citations=Count('id', filter=Q(days_after_retraction__gt=0))
        )
        context.update(citation_stats)
        
        # Get all sidebar statistics in optimized bulk queries
        sidebar_stats = self._get_sidebar_statistics()
        context.update(sidebar_stats)
        
        # Latest citing papers with optimized query
        context['latest_citing_papers'] = Citation.objects.select_related(
            'citing_paper', 'retracted_paper'
        ).filter(
            citing_paper__publication_date__isnull=False
        ).order_by('-citing_paper__publication_date')[:10]
        
        # Top 3 most problematic papers for home page
        context['top_problematic_papers'] = self._get_top_problematic_papers()
        
        return context
    
    def _get_sidebar_statistics(self):
        """Get all sidebar statistics in optimized bulk queries"""
        stats = {}
        
        # Top reasons with optimized processing
        stats['top_reasons'] = self._get_top_reasons()
        

        
        # Exclude "NA" from institutions specifically
        stats['top_institutions'] = RetractedPaper.objects.exclude(
            Q(institution__isnull=True) | Q(institution__exact='') | Q(institution__exact='NA')
        ).values('institution').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        

        
        # Get top publishers, countries, subjects, journals efficiently
        stats['top_publishers'] = RetractedPaper.objects.exclude(
            Q(publisher__isnull=True) | Q(publisher__exact='')
        ).values('publisher').annotate(count=Count('id')).order_by('-count')[:5]
        
        stats['top_countries'] = RetractedPaper.objects.exclude(
            Q(country__isnull=True) | Q(country__exact='')
        ).values('country').annotate(count=Count('id')).order_by('-count')[:5]
        
        stats['top_subjects'] = RetractedPaper.objects.exclude(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).values('subject').annotate(count=Count('id')).order_by('-count')[:5]
        
        stats['top_journals'] = RetractedPaper.objects.exclude(
            Q(journal__isnull=True) | Q(journal__exact='')
        ).values('journal').annotate(count=Count('id')).order_by('-count')[:5]
        
        # Top authors with optimized database processing
        stats['top_authors'] = self._get_top_authors_optimized()
        
        return stats
    
    def _get_top_reasons(self):
        """Get top retraction reasons with optimized processing"""
        from collections import Counter
        
        # Get all reasons in one query
        all_reasons = RetractedPaper.objects.exclude(
            Q(reason__isnull=True) | Q(reason__exact='')
        ).values_list('reason', flat=True)
        
        # Process efficiently in memory (still faster than multiple DB queries)
        reason_counts = Counter()
        for raw_reason in all_reasons:
            if raw_reason:
                # Split and clean reasons
                individual_reasons = [
                    r.strip().lstrip('+').strip()
                    for r in raw_reason.split(';')
                    if r.strip().lstrip('+').strip()
                ]
                for reason in individual_reasons:
                    if reason:
                        reason_counts[reason] += 1
        
        # Return top 5
        return [
            {'reason': reason, 'count': count}
            for reason, count in reason_counts.most_common(5)
        ]
    
    def _get_top_authors_optimized(self):
        """Get top authors with optimized processing"""
        from collections import Counter
        
        # Get all authors in one query  
        all_authors = RetractedPaper.objects.exclude(
            Q(author__isnull=True) | Q(author__exact='')
        ).values_list('author', flat=True)
        
        # Process efficiently in memory
        author_counts = Counter()
        for authors_string in all_authors:
            if authors_string:
                # Split by semicolon and clean up each author name
                individual_authors = [
                    author.strip() 
                    for author in authors_string.split(';') 
                    if author.strip() and len(author.strip()) > 2
                ]
                for author in individual_authors:
                    if author:
                        author_counts[author] += 1
        
        # Return top 5
        return [
            {'author': author, 'count': count}
            for author, count in author_counts.most_common(5)
        ]
    
    def _get_top_problematic_papers(self):
        """Get top 3 most problematic papers (highest post-retraction citations)"""
        top_problematic_papers = RetractedPaper.objects.annotate(
            post_retraction_count=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            total_citation_count=Count('citations')
        ).filter(
            post_retraction_count__gt=0,
            record_id__isnull=False
        ).exclude(record_id__exact='').order_by('-post_retraction_count')[:3]
        
        problematic_papers = []
        for paper in top_problematic_papers:
            citation_rate = 0
            if paper.total_citation_count > 0:
                citation_rate = (paper.post_retraction_count / paper.total_citation_count) * 100
            
            # Parse countries from semicolon-separated string
            countries = []
            country_count = 0
            if paper.country:
                raw_countries = [c.strip() for c in paper.country.split(';') if c.strip()]
                countries = raw_countries[:3]  # Limit to first 3 countries for display
                country_count = len(raw_countries)
            
            problematic_papers.append({
                'paper': paper,
                'post_retraction_citations': paper.post_retraction_count,
                'total_citations': paper.total_citation_count,
                'citation_rate': citation_rate,
                'countries': countries,
                'country_count': country_count,
                'days_since_retraction': paper.days_since_retraction
            })
        
        return problematic_papers


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
        broad_subject = self.request.GET.get('broad_subject', '').strip()
        reason = self.request.GET.get('reason', '').strip()
        country = self.request.GET.get('country', '').strip()
        institution = self.request.GET.get('institution', '').strip()
        author = self.request.GET.get('author', '').strip()
        publisher = self.request.GET.get('publisher', '').strip()
        
        # Advanced filters
        min_citations = self.request.GET.get('min_citations', '').strip()
        max_citations = self.request.GET.get('max_citations', '').strip()
        min_post_retraction = self.request.GET.get('min_post_retraction', '').strip()
        has_post_retraction = self.request.GET.get('has_post_retraction', '').strip()
        
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
        
        if broad_subject:
            # Filter by broad subject category using the parsed subjects
            filtered_ids = []
            for paper in queryset:
                if broad_subject.lower() in [cat.lower() for cat in paper.broad_subject_categories]:
                    filtered_ids.append(paper.id)
            queryset = queryset.filter(id__in=filtered_ids)
        
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
        
        # Advanced citation filters
        if min_citations:
            try:
                min_citations = int(min_citations)
                queryset = queryset.annotate(
                    total_citations=Count('citations')
                ).filter(total_citations__gte=min_citations)
            except ValueError:
                pass
        
        if max_citations:
            try:
                max_citations = int(max_citations)
                queryset = queryset.annotate(
                    total_citations=Count('citations')
                ).filter(total_citations__lte=max_citations)
            except ValueError:
                pass
        
        if min_post_retraction:
            try:
                min_post_retraction = int(min_post_retraction)
                queryset = queryset.annotate(
                    post_retraction_citations=Count(
                        'citations', filter=Q(citations__days_after_retraction__gt=0)
                    )
                ).filter(post_retraction_citations__gte=min_post_retraction)
            except ValueError:
                pass
        
        if has_post_retraction == 'yes':
            queryset = queryset.annotate(
                post_retraction_citations=Count(
                    'citations', filter=Q(citations__days_after_retraction__gt=0)
                )
            ).filter(post_retraction_citations__gt=0)
        elif has_post_retraction == 'no':
            queryset = queryset.annotate(
                post_retraction_citations=Count(
                    'citations', filter=Q(citations__days_after_retraction__gt=0)
                )
            ).filter(post_retraction_citations=0)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Current filter values for preserving form state
        search_query = self.request.GET.get('q', '')
        context['journal_filter'] = self.request.GET.get('journal', '')
        context['year_from'] = self.request.GET.get('year_from', '')
        context['year_to'] = self.request.GET.get('year_to', '')
        context['subject_filter'] = self.request.GET.get('subject', '')
        context['broad_subject_filter'] = self.request.GET.get('broad_subject', '')
        context['reason_filter'] = self.request.GET.get('reason', '')
        context['country_filter'] = self.request.GET.get('country', '')
        context['institution_filter'] = self.request.GET.get('institution', '')
        context['author_filter'] = self.request.GET.get('author', '')
        context['publisher_filter'] = self.request.GET.get('publisher', '')
        
        # Advanced filter values
        context['min_citations'] = self.request.GET.get('min_citations', '')
        context['max_citations'] = self.request.GET.get('max_citations', '')
        context['min_post_retraction'] = self.request.GET.get('min_post_retraction', '')
        context['has_post_retraction'] = self.request.GET.get('has_post_retraction', '')
        
        # If no main search query but other filters exist, populate search box
        if not search_query:
            # Priority order: author, journal, institution, publisher
            if context['author_filter']:
                search_query = context['author_filter']
            elif context['journal_filter']:
                search_query = context['journal_filter']
            elif context['institution_filter']:
                search_query = context['institution_filter']
            elif context['publisher_filter']:
                search_query = context['publisher_filter']
        
        context['search_query'] = search_query
        
        # Get dropdown options efficiently - limit to most common values
        context['subjects'] = RetractedPaper.objects.values_list(
            'subject', flat=True
        ).distinct().exclude(
            Q(subject__isnull=True) | Q(subject__exact='')
        ).order_by('subject')[:100]  # Limit to prevent huge dropdowns
        
        context['reasons'] = RetractedPaper.objects.values_list(
            'reason', flat=True
        ).distinct().exclude(
            Q(reason__isnull=True) | Q(reason__exact='')
        ).order_by('reason')[:100]  # Limit to prevent huge dropdowns
        
        # Get countries efficiently with caching
        context['countries'] = self._get_countries_list()
        
        # Publishers - limit to most common ones
        context['publishers'] = RetractedPaper.objects.values_list(
            'publisher', flat=True
        ).distinct().exclude(
            Q(publisher__isnull=True) | Q(publisher__exact='')
        ).order_by('publisher')[:100]  # Limit to prevent huge dropdowns
        
        return context
    
    def _get_countries_list(self):
        """Get list of countries efficiently"""
        # Use database aggregation to get unique countries
        country_data = RetractedPaper.objects.exclude(
            Q(country__isnull=True) | Q(country__exact='')
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:50]  # Limit to top 50 countries
        
        # Extract individual countries from semicolon-separated strings
        all_countries = set()
        for item in country_data:
            if item['country']:
                countries = [c.strip() for c in item['country'].split(';')]
                all_countries.update(countries)
        
        # Remove invalid entries and sort
        invalid_entries = {'', 'Unknown', 'unknown', 'N/A', 'n/a', 'None', 'null'}
        clean_countries = sorted(list(all_countries - invalid_entries))[:100]
        return clean_countries


class ExportSearchView(View):
    """Export search results to CSV or Excel format"""
    
    def get(self, request):
        import csv
        import io
        from django.http import HttpResponse
        
        # Get the same queryset as SearchView
        search_view = SearchView()
        search_view.request = request
        queryset = search_view.get_queryset()
        
        # Get export format
        export_format = request.GET.get('format', 'csv').lower()
        
        if export_format == 'excel':
            return self._export_excel(queryset)
        else:
            return self._export_csv(queryset)
    
    def _export_csv(self, queryset):
        import csv
        import io
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="retracted_papers_search.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = [
            'Record ID', 'Title', 'Authors', 'Journal', 'Publisher',
            'Original Paper Date', 'Retraction Date', 'Retraction Reason',
            'Subject', 'Country', 'Institution', 'DOI',
            'Total Citations', 'Post-Retraction Citations', 'Open Access'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for paper in queryset[:1000]:  # Limit to 1000 rows for performance
            # Calculate citation counts
            total_citations = paper.citations.count()
            post_retraction_citations = paper.citations.filter(days_after_retraction__gt=0).count()
            
            row = [
                paper.record_id or '',
                paper.title or '',
                paper.author or '',
                paper.journal or '',
                paper.publisher or '',
                paper.original_paper_date.strftime('%Y-%m-%d') if paper.original_paper_date else '',
                paper.retraction_date.strftime('%Y-%m-%d') if paper.retraction_date else '',
                paper.reason or '',
                paper.subject or '',
                paper.country or '',
                paper.institution or '',
                paper.original_paper_doi or '',
                total_citations,
                post_retraction_citations,
                'Yes' if paper.is_open_access else 'No'
            ]
            writer.writerow(row)
        
        return response
    
    def _export_excel(self, queryset):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
            from django.http import HttpResponse
            import io
        except ImportError:
            # Fallback to CSV if openpyxl is not available
            return self._export_csv(queryset)
        
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Retracted Papers Search Results"
        
        # Define headers
        headers = [
            'Record ID', 'Title', 'Authors', 'Journal', 'Publisher',
            'Original Paper Date', 'Retraction Date', 'Retraction Reason',
            'Subject', 'Country', 'Institution', 'DOI',
            'Total Citations', 'Post-Retraction Citations', 'Open Access'
        ]
        
        # Add headers with styling
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Add data rows
        for row_num, paper in enumerate(queryset[:1000], 2):  # Start from row 2
            # Calculate citation counts
            total_citations = paper.citations.count()
            post_retraction_citations = paper.citations.filter(days_after_retraction__gt=0).count()
            
            row_data = [
                paper.record_id or '',
                paper.title or '',
                paper.author or '',
                paper.journal or '',
                paper.publisher or '',
                paper.original_paper_date.strftime('%Y-%m-%d') if paper.original_paper_date else '',
                paper.retraction_date.strftime('%Y-%m-%d') if paper.retraction_date else '',
                paper.reason or '',
                paper.subject or '',
                paper.country or '',
                paper.institution or '',
                paper.original_paper_doi or '',
                total_citations,
                post_retraction_citations,
                'Yes' if paper.is_open_access else 'No'
            ]
            
            for col, value in enumerate(row_data, 1):
                ws.cell(row=row_num, column=col, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="retracted_papers_search.xlsx"'
        
        return response


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


class AnalyticsView(View):
    """Optimized analytics dashboard with efficient database queries"""
    template_name = 'papers/analytics.html'
    
    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def get_context_data(self, **kwargs):
        context = {}
        
        # Get all basic stats in one efficient query
        context.update(self._get_basic_stats())
        
        # Get analytics data efficiently
        context.update(self._get_analytics_data())
        
        return context
    
    def _get_basic_stats(self):
        """Get basic statistics in efficient bulk queries"""
        # Get all basic counts in one go
        paper_stats = RetractedPaper.objects.aggregate(
            total_papers=Count('id'),
            recent_retractions=Count('id', filter=Q(
                retraction_date__gte=timezone.now().date() - timedelta(days=365)
            )),
            avg_citations_per_paper=Avg('citation_count')
        )
        
        # Calculate statistics for papers with citations only (to avoid the 0-skew)
        citation_counts_nonzero = list(RetractedPaper.objects.filter(citation_count__gt=0).values_list('citation_count', flat=True))
        
        if citation_counts_nonzero and len(citation_counts_nonzero) >= 4:
            import statistics
            paper_stats['median_citations_per_paper'] = statistics.median(citation_counts_nonzero)
            paper_stats['stdev_citations_per_paper'] = statistics.stdev(citation_counts_nonzero)
            
            # Calculate Q1 and Q3 for papers WITH citations
            quantiles = statistics.quantiles(citation_counts_nonzero, n=4)
            paper_stats['q1_citations_per_paper'] = quantiles[0]  # 25th percentile (Q1)
            paper_stats['q3_citations_per_paper'] = quantiles[2]  # 75th percentile (Q3)
        else:
            paper_stats['median_citations_per_paper'] = 0
            paper_stats['stdev_citations_per_paper'] = 0
            paper_stats['q1_citations_per_paper'] = 0
            paper_stats['q3_citations_per_paper'] = 0
        
        # Get citation stats efficiently
        citation_stats = Citation.objects.aggregate(
            total_citations=Count('id'),
            post_retraction_citations=Count('id', filter=Q(days_after_retraction__gt=0)),
            pre_retraction_citations=Count('id', filter=Q(days_after_retraction__lt=0)),
            same_day_citations=Count('id', filter=Q(days_after_retraction=0))
        )
        
        # Calculate percentages
        total_citations = citation_stats['total_citations']
        post_retraction = citation_stats['post_retraction_citations']
        
        stats = {
            'stats': {
                **paper_stats,
                **citation_stats,
                'post_retraction_percentage': (post_retraction / max(total_citations, 1)) * 100
            }
        }
        
        # Post-retraction timeline analysis in one query
        stats['post_retraction_timeline'] = Citation.objects.filter(
            days_after_retraction__gt=0
        ).aggregate(
            within_30_days=Count('id', filter=Q(days_after_retraction__lte=30)),
            within_6_months=Count('id', filter=Q(days_after_retraction__lte=180)),
            within_1_year=Count('id', filter=Q(days_after_retraction__lte=365)),
            within_2_years=Count('id', filter=Q(days_after_retraction__lte=730)),
            after_2_years=Count('id', filter=Q(days_after_retraction__gt=730))
        )
        
        # Citation patterns
        stats['citation_patterns'] = {
            'post_retraction': post_retraction,
            'pre_retraction': citation_stats['pre_retraction_citations'],
            'same_day': citation_stats['same_day_citations'],
            'post_retraction_percentage': (post_retraction / max(total_citations, 1)) * 100
        }
        
        return stats
    
    def _get_analytics_data(self):
        """Get analytics data with optimized queries"""
        data = {}
        
        # Retractions by year - use publication_year since retraction_date seems empty
        from django.db.models.functions import TruncYear
        
        # First try with publication_year since retraction_date appears to be empty in database
        publication_years = RetractedPaper.objects.filter(
            publication_year__isnull=False
        ).values('publication_year').annotate(
            count=Count('id')
        ).order_by('publication_year')[:30]
        
        data['retraction_years'] = [
            {
                'year': item['publication_year'],
                'count': item['count']
            }
            for item in publication_years if item['publication_year']
        ]
        
        # If still no data, try retraction_date as fallback
        if not data['retraction_years']:
            retraction_years = RetractedPaper.objects.filter(
                retraction_date__isnull=False
            ).annotate(
                year=TruncYear('retraction_date')
            ).values('year').annotate(
                count=Count('id')
            ).order_by('year')[:30]
            
            data['retraction_years'] = [
                {
                    'year': item['year'].year if item['year'] else 'Unknown',
                    'count': item['count']
                }
                for item in retraction_years
            ]
        
        # Top journals with efficient query (limit complexity)
        data['top_journals'] = RetractedPaper.objects.values(
            'journal'
        ).annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).exclude(
            journal__isnull=True
        ).exclude(
            journal__exact=''
        ).order_by('-post_retraction_citations')[:10]
        
        # Top subjects with efficient query
        data['top_subjects'] = RetractedPaper.objects.values(
            'subject'
        ).annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).exclude(
            subject__isnull=True
        ).exclude(
            subject__exact=''
        ).order_by('-post_retraction_citations')[:10]
        
        # Papers with most post-retraction citations (optimized)
        data['most_cited_post_retraction'] = RetractedPaper.objects.annotate(
            post_retraction_count=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).filter(
            post_retraction_count__gt=0,
            record_id__isnull=False
        ).exclude(
            record_id__exact=''
        ).order_by('-post_retraction_count')[:10]
        
        # Recent import logs
        data['recent_imports'] = DataImportLog.objects.order_by('-start_time')[:5]
        
        # Monthly post-retraction trends (simplified)
        from django.db.models.functions import TruncMonth
        monthly_data = Citation.objects.filter(
            days_after_retraction__gt=0,
            created_at__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')[:12]  # Limit to 12 months
        
        data['monthly_post_retraction'] = [
            {
                'month': item['month'].strftime('%Y-%m') if item['month'] else 'Unknown',
                'count': item['count']
            }
            for item in monthly_data
        ]
        
        # Add missing chart data structures
        data.update(self._get_chart_data())
        
        return data
    
    def _get_chart_data(self):
        """Get additional chart data that was removed"""
        chart_data = {}
        
        # Access analytics for open access chart
        access_stats = RetractedPaper.objects.aggregate(
            open_access_count=Count('id', filter=Q(is_open_access=True)),
            paywalled_count=Count('id', filter=Q(paywalled=True)),
            unknown_count=Count('id', filter=Q(is_open_access=False, paywalled=False))
        )
        
        # Post-retraction citations by access type
        oa_post_citations = Citation.objects.filter(
            retracted_paper__is_open_access=True,
            days_after_retraction__gt=0
        ).count()
        
        paywalled_post_citations = Citation.objects.filter(
            retracted_paper__paywalled=True,
            days_after_retraction__gt=0
        ).count()
        
        unknown_post_citations = Citation.objects.filter(
            retracted_paper__is_open_access=False,
            retracted_paper__paywalled=False,
            days_after_retraction__gt=0
        ).count()
        
        total_papers = access_stats['open_access_count'] + access_stats['paywalled_count'] + access_stats['unknown_count']
        
        chart_data['access_analytics'] = {
            'open_access': {
                'count': access_stats['open_access_count'],
                'post_retraction_citations': oa_post_citations,
                'percentage': (access_stats['open_access_count'] / max(total_papers, 1)) * 100,
                'citations_per_paper': oa_post_citations / max(access_stats['open_access_count'], 1)
            },
            'paywalled': {
                'count': access_stats['paywalled_count'],
                'post_retraction_citations': paywalled_post_citations,
                'percentage': (access_stats['paywalled_count'] / max(total_papers, 1)) * 100,
                'citations_per_paper': paywalled_post_citations / max(access_stats['paywalled_count'], 1)
            },
            'unknown': {
                'count': access_stats['unknown_count'],
                'post_retraction_citations': unknown_post_citations,
                'percentage': (access_stats['unknown_count'] / max(total_papers, 1)) * 100,
                'citations_per_paper': unknown_post_citations / max(access_stats['unknown_count'], 1)
            }
        }
        
        # Country analytics with proper parsing of semicolon-separated countries
        from django.db.models import CharField
        from django.db.models.functions import Trim
        
        # Get all papers with countries and split semicolon-separated values
        papers_with_countries = RetractedPaper.objects.exclude(
            country__isnull=True
        ).exclude(country__exact='').values_list('id', 'country', 'is_open_access')
        
        # Parse individual countries from semicolon-separated strings
        country_stats = {}
        for paper_id, country_string, is_open_access in papers_with_countries:
            if country_string:
                # Split by semicolon and clean up country names
                countries = [c.strip() for c in country_string.split(';') if c.strip()]
                for country in countries:
                    if country not in country_stats:
                        country_stats[country] = {
                            'retraction_count': 0,
                            'open_access_count': 0,
                            'paper_ids': set()
                        }
                    
                    # Only count each paper once per country
                    if paper_id not in country_stats[country]['paper_ids']:
                        country_stats[country]['retraction_count'] += 1
                        country_stats[country]['paper_ids'].add(paper_id)
                        if is_open_access:
                            country_stats[country]['open_access_count'] += 1
        
        # Calculate post-retraction citations for each country (batched to avoid SQLite limit)
        for country in country_stats:
            country_paper_ids = list(country_stats[country]['paper_ids'])
            post_retraction_citations = 0
            
            # Process in batches of 500 to avoid SQLite variable limit
            batch_size = 500
            for i in range(0, len(country_paper_ids), batch_size):
                batch_ids = country_paper_ids[i:i + batch_size]
                batch_count = Citation.objects.filter(
                    retracted_paper_id__in=batch_ids,
                    days_after_retraction__gt=0
                ).count()
                post_retraction_citations += batch_count
                
            country_stats[country]['post_retraction_citations'] = post_retraction_citations
            country_stats[country]['open_access_percentage'] = (
                country_stats[country]['open_access_count'] / 
                max(country_stats[country]['retraction_count'], 1)
            ) * 100
        
        # Convert to list format and sort by retraction count
        country_analytics_list = []
        for country, stats in country_stats.items():
            country_analytics_list.append({
                'country': country,
                'retraction_count': stats['retraction_count'],
                'post_retraction_citations': stats['post_retraction_citations'],
                'open_access_count': stats['open_access_count'],
                'open_access_percentage': stats['open_access_percentage']
            })
        
        country_analytics_list.sort(key=lambda x: x['retraction_count'], reverse=True)
        chart_data['country_analytics'] = country_analytics_list
        
        # World map data with logarithmic scaling for choropleth map
        import math
        world_map_data = []
        
        # Create ISO alpha-3 country code mapping for Plotly choropleth compatibility
        country_iso_mapping = {
            'United States': 'USA',
            'USA': 'USA', 
            'US': 'USA',
            'United States of America': 'USA',
            'China': 'CHN',
            'India': 'IND',
            'Germany': 'DEU',
            'United Kingdom': 'GBR',
            'UK': 'GBR',
            'Japan': 'JPN',
            'France': 'FRA',
            'Canada': 'CAN',
            'Australia': 'AUS',
            'Brazil': 'BRA',
            'Italy': 'ITA',
            'Spain': 'ESP',
            'South Korea': 'KOR',
            'Republic of Korea': 'KOR',
            'Netherlands': 'NLD',
            'Turkey': 'TUR',
            'Iran': 'IRN',
            'Islamic Republic of Iran': 'IRN',
            'Israel': 'ISR',
            'South Africa': 'ZAF',
            'Switzerland': 'CHE',
            'Sweden': 'SWE',
            'Norway': 'NOR',
            'Denmark': 'DNK',
            'Finland': 'FIN',
            'Poland': 'POL',
            'Austria': 'AUT',
            'Belgium': 'BEL',
            'Mexico': 'MEX',
            'Argentina': 'ARG',
            'Chile': 'CHL',
            'Russia': 'RUS',
            'Russian Federation': 'RUS',
            'Saudi Arabia': 'SAU',
            'Egypt': 'EGY',
            'Thailand': 'THA',
            'Malaysia': 'MYS',
            'Singapore': 'SGP',
            'Indonesia': 'IDN',
            'Philippines': 'PHL',
            'Vietnam': 'VNM',
            'Pakistan': 'PAK',
            'Bangladesh': 'BGD',
            'Nigeria': 'NGA',
            'North Korea': 'PRK',
            'Taiwan': 'TWN',
            'Czech Republic': 'CZE',
            'Czechia': 'CZE',
            'Greece': 'GRC',
            'Portugal': 'PRT',
            'Ireland': 'IRL',
            'New Zealand': 'NZL'
        }
        
        for item in country_analytics_list:
            retraction_count = item['retraction_count']
            # Apply log scaling for better color distribution
            log_value = math.log10(max(retraction_count, 1))
            
            # Map country name to ISO alpha-3 code for Plotly choropleth
            country_name = item['country']
            iso_code = country_iso_mapping.get(country_name)  # Remove explicit None
            
            world_map_data.append({
                'country': country_name,  # Original name for display
                'iso_alpha': iso_code if iso_code else '',  # Convert None to empty string
                'value': retraction_count,
                'log_value': log_value,
                'post_retraction_citations': item['post_retraction_citations'],
                'open_access_percentage': item['open_access_percentage']
            })
        
        chart_data['world_map_data'] = world_map_data
        
        # Journal bubble chart data
        journal_impact = RetractedPaper.objects.values('journal').annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            total_citations=Sum('citation_count')
        ).filter(
            retraction_count__gte=5,  # At least 5 retractions for meaningful data
            journal__isnull=False,
            post_retraction_citations__gt=0  # Must have post-retraction citations
        ).exclude(journal__exact='').order_by('-post_retraction_citations')[:25]
        
        chart_data['journal_bubble_data'] = [
            {
                'journal': item['journal'][:30] + '...' if len(item['journal']) > 30 else item['journal'],
                'x': item['retraction_count'],
                'y': item['post_retraction_citations'] or 0,
                'size': max(8, min(50, item['retraction_count'])),  # Better size scaling
                'impact_score': (item['post_retraction_citations'] or 0) / max(item['retraction_count'], 1),  # Citations per retraction
                'total_citations': item['total_citations'] or 0
            }
            for item in journal_impact
        ]
        
        # Article type analytics
        article_type_analytics = RetractedPaper.objects.exclude(
            article_type__isnull=True
        ).exclude(article_type__exact='').values('article_type').annotate(
            count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).order_by('-count')[:10]
        
        chart_data['article_type_analytics'] = [
            {
                'type': item['article_type'],
                'count': item['count'],
                'post_retraction_citations': item['post_retraction_citations'],
                'citation_rate': (item['post_retraction_citations'] / max(item['count'], 1)) * 100
            }
            for item in article_type_analytics
        ]
        
        # Publisher analytics
        publisher_analytics = RetractedPaper.objects.exclude(
            publisher__isnull=True
        ).exclude(publisher__exact='').values('publisher').annotate(
            retraction_count=Count('id'),
            post_retraction_citations=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            )
        ).order_by('-retraction_count')[:10]
        
        chart_data['publisher_analytics'] = [
            {
                'publisher': item['publisher'][:40],  # Truncate long names
                'retraction_count': item['retraction_count'],
                'post_retraction_citations': item['post_retraction_citations']
            }
            for item in publisher_analytics
        ]
        
        # Problematic papers with detailed info
        top_problematic_papers = RetractedPaper.objects.annotate(
            post_retraction_count=Count(
                'citations', filter=Q(citations__days_after_retraction__gt=0)
            ),
            total_citation_count=Count('citations')
        ).filter(
            post_retraction_count__gt=0,
            record_id__isnull=False
        ).exclude(record_id__exact='').order_by('-post_retraction_count')[:20]
        
        chart_data['problematic_papers_detailed'] = []
        for paper in top_problematic_papers:
            citation_rate = 0
            if paper.total_citation_count > 0:
                citation_rate = (paper.post_retraction_count / paper.total_citation_count) * 100
            
            # Parse countries from semicolon-separated string
            countries = []
            country_count = 0
            if paper.country:
                raw_countries = [c.strip() for c in paper.country.split(';') if c.strip()]
                countries = raw_countries[:3]  # Limit to first 3 countries for display
                country_count = len(raw_countries)
            
            chart_data['problematic_papers_detailed'].append({
                'record_id': paper.record_id,
                'title': paper.title[:60] + '...' if len(paper.title) > 60 else paper.title,
                'journal': paper.journal,
                'country': paper.country,      # Keep raw for searching
                'countries': countries,        # Parsed list for display
                'country_count': country_count, # Total count for "X more" display
                'institution': paper.institution[:50] + '...' if paper.institution and len(paper.institution) > 50 else paper.institution,
                'retraction_date': paper.retraction_date.strftime('%Y-%m-%d') if paper.retraction_date else None,
                'days_since_retraction': paper.days_since_retraction,
                'post_retraction_citations': paper.post_retraction_count,
                'total_citations': paper.total_citation_count,
                'citation_rate': citation_rate,
                'access_status': paper.access_status,
                'formatted_reasons': paper.formatted_reasons,
                'formatted_subjects': paper.formatted_subjects,
                'original_paper_url': paper.original_paper_url,
                'pubmed_url': paper.pubmed_url
            })
        
        # Add missing chart data that JavaScript expects
        chart_data.update(self._get_missing_chart_data())
        
        # Ensure all required data has fallback values
        chart_data.setdefault('retraction_years', [])
        chart_data.setdefault('retraction_comparison', [])
        chart_data.setdefault('subject_donut_data', [])
        chart_data.setdefault('citation_timing_distribution', [])
        chart_data.setdefault('journal_bubble_data', [])
        chart_data.setdefault('citation_heatmap', [])
        chart_data.setdefault('sunburst_data', {'name': 'No Data', 'children': []})
        chart_data.setdefault('network_data', {'nodes': [], 'links': []})
        chart_data.setdefault('world_map_data', [])
        chart_data.setdefault('country_analytics', [])
        chart_data.setdefault('article_type_data', [])
        chart_data.setdefault('publisher_data', [])
        chart_data.setdefault('access_analytics', {'open_access': {'count': 0}, 'paywalled': {'count': 0}, 'unknown': {'count': 0}})
        
        return chart_data
    
    def _get_missing_chart_data(self):
        """Get additional chart data that the template expects but was missing"""
        missing_data = {}
        
        # Retraction comparison data (before vs after retraction by year)
        from django.db.models.functions import TruncYear
        retraction_comparison = []
        
        retraction_years = RetractedPaper.objects.filter(
            retraction_date__isnull=False
        ).annotate(
            year=TruncYear('retraction_date')
        ).values('year').annotate(
            retracted_count=Count('id'),
            pre_retraction_citations=Count('citations', filter=Q(citations__days_after_retraction__lt=0)),
            post_retraction_citations=Count('citations', filter=Q(citations__days_after_retraction__gt=0)),
            same_day_citations=Count('citations', filter=Q(citations__days_after_retraction=0))
        ).order_by('year')[:10]
        
        for item in retraction_years:
            retraction_comparison.append({
                'year': item['year'].year if item['year'] else 'Unknown',
                'pre_retraction': item['pre_retraction_citations'],
                'post_retraction': item['post_retraction_citations'],
                'same_day': item['same_day_citations']
            })
        
        missing_data['retraction_comparison'] = retraction_comparison
        
        # Subject donut data for distribution chart
        subjects = RetractedPaper.objects.values('subject').annotate(
            count=Count('id')
        ).filter(
            subject__isnull=False
        ).exclude(
            subject__exact=''
        ).order_by('-count')[:8]
        
        missing_data['subject_donut_data'] = [
            {
                'subject': item['subject'][:30] + '...' if len(item['subject']) > 30 else item['subject'],
                'count': item['count'],
                'full_subject': item['subject']
            }
            for item in subjects
        ]
        
        # Citation timing distribution
        timing_data = Citation.objects.filter(
            days_after_retraction__isnull=False
        ).aggregate(
            pre_retraction=Count('id', filter=Q(days_after_retraction__lt=0)),
            same_day=Count('id', filter=Q(days_after_retraction=0)),
            within_30_days=Count('id', filter=Q(days_after_retraction__gt=0, days_after_retraction__lte=30)),
            within_6_months=Count('id', filter=Q(days_after_retraction__gt=30, days_after_retraction__lte=180)),
            within_1_year=Count('id', filter=Q(days_after_retraction__gt=180, days_after_retraction__lte=365)),
            after_1_year=Count('id', filter=Q(days_after_retraction__gt=365))
        )
        
        missing_data['citation_timing_distribution'] = [
            {'days': -30, 'count': timing_data['pre_retraction']},
            {'days': 0, 'count': timing_data['same_day']},
            {'days': 30, 'count': timing_data['within_30_days']},
            {'days': 180, 'count': timing_data['within_6_months']},
            {'days': 365, 'count': timing_data['within_1_year']},
            {'days': 730, 'count': timing_data['after_1_year']}
        ]
        
        # Network data with connections
        network_nodes = []
        network_links = []
        
        # Add journal nodes
        top_journals = RetractedPaper.objects.values('journal').annotate(
            count=Count('id'),
            post_retraction_citations=Count('citations', filter=Q(citations__days_after_retraction__gt=0))
        ).filter(journal__isnull=False).exclude(journal__exact='').order_by('-count')[:12]
        
        for i, journal in enumerate(top_journals):
            network_nodes.append({
                'id': f"journal_{i}",
                'name': journal['journal'][:20] + '...' if len(journal['journal']) > 20 else journal['journal'],
                'type': 'journal',
                'size': max(8, min(30, journal['count'] / 10)),
                'full_name': journal['journal'],
                'retraction_count': journal['count'],
                'post_retraction_citations': journal['post_retraction_citations']
            })
        
        # Add country nodes
        top_countries = RetractedPaper.objects.values('country').annotate(
            count=Count('id')
        ).filter(country__isnull=False).exclude(country__exact='').order_by('-count')[:8]
        
        for i, country in enumerate(top_countries):
            # Handle semicolon-separated countries by taking the first one
            country_name = country['country'].split(';')[0].strip() if ';' in country['country'] else country['country']
            network_nodes.append({
                'id': f"country_{i}",
                'name': country_name[:15] + '...' if len(country_name) > 15 else country_name,
                'type': 'country',
                'size': max(8, min(25, country['count'] / 20)),
                'full_name': country_name,
                'retraction_count': country['count']
            })
        
        # Add subject nodes
        top_subjects = RetractedPaper.objects.values('subject').annotate(
            count=Count('id')
        ).filter(subject__isnull=False).exclude(subject__exact='').order_by('-count')[:6]
        
        for i, subject in enumerate(top_subjects):
            network_nodes.append({
                'id': f"subject_{i}",
                'name': subject['subject'][:15] + '...' if len(subject['subject']) > 15 else subject['subject'],
                'type': 'subject',
                'size': max(8, min(20, subject['count'] / 30)),
                'full_name': subject['subject'],
                'retraction_count': subject['count']
            })
        
        # Create network links based on co-occurrence
        # Link journals to countries where they publish retractions
        journal_country_links = RetractedPaper.objects.values('journal', 'country').annotate(
            count=Count('id')
        ).filter(
            journal__in=[j['journal'] for j in top_journals],
            country__in=[c['country'] for c in top_countries],
            count__gte=2  # At least 2 papers in common
        )[:20]
        
        for link in journal_country_links:
            journal_idx = next((i for i, j in enumerate(top_journals) if j['journal'] == link['journal']), None)
            country_idx = next((i for i, c in enumerate(top_countries) if c['country'] == link['country']), None)
            
            if journal_idx is not None and country_idx is not None:
                network_links.append({
                    'source': f"journal_{journal_idx}",
                    'target': f"country_{country_idx}",
                    'value': link['count'],
                    'type': 'journal-country'
                })
        
        # Link subjects to journals
        subject_journal_links = RetractedPaper.objects.values('subject', 'journal').annotate(
            count=Count('id')
        ).filter(
            subject__in=[s['subject'] for s in top_subjects],
            journal__in=[j['journal'] for j in top_journals],
            count__gte=2  # At least 2 papers in common
        )[:15]
        
        for link in subject_journal_links:
            subject_idx = next((i for i, s in enumerate(top_subjects) if s['subject'] == link['subject']), None)
            journal_idx = next((i for i, j in enumerate(top_journals) if j['journal'] == link['journal']), None)
            
            if subject_idx is not None and journal_idx is not None:
                network_links.append({
                    'source': f"subject_{subject_idx}",
                    'target': f"journal_{journal_idx}",
                    'value': link['count'],
                    'type': 'subject-journal'
                })
        
        missing_data['network_data'] = {
            'nodes': network_nodes,
            'links': network_links
        }
        
        # Citation heatmap data (by month and days after retraction)
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
        missing_data['citation_heatmap'] = citation_heatmap
        
        # Add article type analysis
        article_type_data = RetractedPaper.objects.values('article_type').annotate(
            count=Count('id')
        ).filter(article_type__isnull=False).exclude(article_type__exact='').order_by('-count')[:10]
        
        missing_data['article_type_data'] = [
            {
                'type': item['article_type'],
                'count': item['count']
            }
            for item in article_type_data
        ]
        
        # Add publisher analysis  
        publisher_data = RetractedPaper.objects.values('publisher').annotate(
            count=Count('id'),
            post_retraction_citations=Count('citations', filter=Q(citations__days_after_retraction__gt=0))
        ).filter(publisher__isnull=False).exclude(publisher__exact='').order_by('-count')[:10]
        
        missing_data['publisher_data'] = [
            {
                'publisher': item['publisher'],
                'count': item['count'],
                'post_retraction_citations': item['post_retraction_citations']
            }
            for item in publisher_data
        ]
        
        # Add open access analysis
        access_data = RetractedPaper.objects.aggregate(
            open_access=Count('id', filter=Q(is_open_access=True)),
            paywalled=Count('id', filter=Q(is_open_access=False)),
            total=Count('id')
        )
        
        missing_data['access_analytics'] = {
            'open_access': {'count': access_data['open_access']},
            'paywalled': {'count': access_data['paywalled']},
            'unknown': {'count': access_data['total'] - access_data['open_access'] - access_data['paywalled']}
        }
        
        # Sunburst chart data for subject hierarchy
        sunburst_data = self._get_sunburst_subject_data()
        missing_data['sunburst_data'] = sunburst_data
        
        return missing_data
    
    def _get_sunburst_subject_data(self):
        """Generate hierarchical subject data for sunburst chart"""
        # Try to use the new database fields first
        papers_with_new_fields = RetractedPaper.objects.exclude(
            broad_subjects__isnull=True
        ).exclude(broad_subjects__exact='').exclude(
            specific_fields__isnull=True
        ).exclude(specific_fields__exact='')
        
        # If we have enough papers with new fields, use them, otherwise fallback to parsing
        if papers_with_new_fields.count() > 100:
            papers_with_subjects = papers_with_new_fields
            use_new_fields = True
        else:
            papers_with_subjects = RetractedPaper.objects.exclude(
                subject__isnull=True
            ).exclude(subject__exact='')
            use_new_fields = False
        
        # Build hierarchy: broad_category -> specific_field -> count
        hierarchy = {}
        
        for paper in papers_with_subjects:
            if use_new_fields:
                # Use new database fields
                broad_subjects = [s.strip() for s in paper.broad_subjects.split(';') if s.strip()] if paper.broad_subjects else []
                specific_fields = [s.strip() for s in paper.specific_fields.split(';') if s.strip()] if paper.specific_fields else []
                
                # Match broad subjects with specific fields
                max_len = max(len(broad_subjects), len(specific_fields), 1)
                
                for i in range(max_len):
                    broad_category = broad_subjects[i] if i < len(broad_subjects) else broad_subjects[0] if broad_subjects else 'Unknown'
                    specific_field = specific_fields[i] if i < len(specific_fields) else 'General'
                    
                    if broad_category not in hierarchy:
                        hierarchy[broad_category] = {}
                    
                    if specific_field not in hierarchy[broad_category]:
                        hierarchy[broad_category][specific_field] = 0
                    
                    hierarchy[broad_category][specific_field] += 1
            else:
                # Fallback to parsing the original subject field
                parsed_subjects = paper.parsed_subjects
                
                for subject_info in parsed_subjects:
                    broad_category = subject_info['broad_category']
                    specific_field = subject_info['specific_field'] or 'General'
                    
                    if broad_category not in hierarchy:
                        hierarchy[broad_category] = {}
                    
                    if specific_field not in hierarchy[broad_category]:
                        hierarchy[broad_category][specific_field] = 0
                    
                    hierarchy[broad_category][specific_field] += 1
        
        # Convert to sunburst format
        sunburst_data = {
            'name': 'All Subjects',
            'children': []
        }
        
        total_count = 0
        for broad_category, fields in hierarchy.items():
            broad_total = sum(fields.values())
            total_count += broad_total
            
            broad_node = {
                'name': broad_category,
                'value': broad_total,
                'children': []
            }
            
            for field, count in fields.items():
                broad_node['children'].append({
                    'name': field,
                    'value': count,
                    'full_name': f"{broad_category} - {field}" if field != 'General' else broad_category
                })
            
            # Sort children by value
            broad_node['children'].sort(key=lambda x: x['value'], reverse=True)
            sunburst_data['children'].append(broad_node)
        
        # Sort broad categories by value
        sunburst_data['children'].sort(key=lambda x: x['value'], reverse=True)
        sunburst_data['value'] = total_count
        
        return sunburst_data


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
            citations_qs = citations_qs.filter(retracted_paper__journal__icontains=journal_filter)
            
        if subject_filter:
            citations_qs = citations_qs.filter(retracted_paper__subject__icontains=subject_filter)
        
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
                        retracted_paper__retraction_date__month=month,
                        days_after_retraction__gt=730
                    ).count()
                else:
                    prev_bucket = 0 if bucket == 30 else [30, 90, 180, 365, 730][month_data.__len__()]
                    count = Citation.objects.filter(
                        retracted_paper__retraction_date__month=month,
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


@cache_page(60)  # Cache for 1 minute
def analytics_data_ajax(request):
    """AJAX endpoint for real-time analytics data updates"""
    
    # Get basic stats
    stats = RetractedPaper.objects.aggregate(
        total_papers=Count('id'),
        total_citations=Count('citations'),
        post_retraction_citations=Count('citations', filter=Q(citations__days_after_retraction__gt=0)),
        recent_retractions=Count('id', filter=Q(retraction_date__gte=timezone.now() - timedelta(days=30)))
    )
    
    # Get recent activity (last 24 hours)
    recent_imports = DataImportLog.objects.filter(
        start_time__gte=timezone.now() - timedelta(hours=24)
    ).aggregate(
        total_imports=Count('id'),
        records_imported=Sum('records_created')
    )
    
    # Quick citation patterns
    citation_patterns = Citation.objects.aggregate(
        post_retraction=Count('id', filter=Q(days_after_retraction__gt=0)),
        pre_retraction=Count('id', filter=Q(days_after_retraction__lt=0)),
        same_day=Count('id', filter=Q(days_after_retraction=0))
    )
    
    return JsonResponse({
        'stats': stats,
        'recent_activity': recent_imports,
        'citation_patterns': citation_patterns,
        'last_updated': timezone.now().isoformat(),
        'status': 'success'
    })
