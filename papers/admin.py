from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RetractedPaper, CitingPaper, Citation, DataImportLog


@admin.register(RetractedPaper)
class RetractedPaperAdmin(admin.ModelAdmin):
    list_display = [
        'record_id', 
        'title_short', 
        'journal', 
        'country', 
        'article_type',
        'access_status_badge',
        'retraction_date', 
        'citation_count',
        'has_post_retraction_citations'
    ]
    
    list_filter = [
        'country',
        'publisher', 
        'article_type',
        'is_open_access',
        'paywalled',
        'retraction_date',
        'original_paper_date',
        ('retraction_date', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'record_id',
        'title', 
        'author', 
        'journal', 
        'publisher',
        'institution',
        'subject',
        'original_paper_doi',
        'reason'
    ]
    
    readonly_fields = [
        'record_id',
        'created_at', 
        'updated_at',
        'citation_count',
        'access_status_badge',
        'original_paper_link',
        'retraction_notice_link',
        'pubmed_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'record_id',
                'title',
                'author',
                'subject'
            )
        }),
        ('Publication Details', {
            'fields': (
                'journal',
                'publisher',
                'original_paper_date',
                'article_type'
            )
        }),
        ('Geographic & Institutional', {
            'fields': (
                'country',
                'institution'
            )
        }),
        ('DOIs and Links', {
            'fields': (
                'original_paper_doi',
                'original_paper_link',
                'retraction_doi',
                'retraction_notice_link',
                'urls'
            )
        }),
        ('PubMed Information', {
            'fields': (
                'original_paper_pubmed_id',
                'retraction_pubmed_id',
                'pubmed_link'
            )
        }),
        ('Retraction Details', {
            'fields': (
                'retraction_date',
                'retraction_nature',
                'reason'
            )
        }),
        ('Access and Availability', {
            'fields': (
                'is_open_access',
                'paywalled',
                'access_status_badge'
            )
        }),
        ('Additional Information', {
            'fields': (
                'abstract',
                'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Citation Tracking', {
            'fields': (
                'citation_count',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_open_access', 'mark_as_paywalled', 'fetch_citations']
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'
    
    def access_status_badge(self, obj):
        if obj.is_open_access:
            return format_html(
                '<span style="color: green; font-weight: bold;">🔓 Open Access</span>'
            )
        elif obj.paywalled:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🔒 Paywalled</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">❓ Unknown</span>'
            )
    access_status_badge.short_description = 'Access Status'
    
    def has_post_retraction_citations(self, obj):
        count = obj.citations.filter(days_after_retraction__gt=0).count()
        if count > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} post-retraction</span>',
                count
            )
        return format_html('<span style="color: green;">✓ No post-retraction</span>')
    has_post_retraction_citations.short_description = 'Post-Retraction Citations'
    
    def original_paper_link(self, obj):
        if obj.original_paper_url:
            return format_html(
                '<a href="{}" target="_blank">🔗 View Original Paper</a>',
                obj.original_paper_url
            )
        return "No DOI available"
    original_paper_link.short_description = 'Original Paper'
    
    def retraction_notice_link(self, obj):
        if obj.retraction_notice_url:
            return format_html(
                '<a href="{}" target="_blank">🔗 View Retraction Notice</a>',
                obj.retraction_notice_url
            )
        return "No retraction DOI available"
    retraction_notice_link.short_description = 'Retraction Notice'
    
    def pubmed_link(self, obj):
        if obj.pubmed_url:
            return format_html(
                '<a href="{}" target="_blank">🔗 View on PubMed</a>',
                obj.pubmed_url
            )
        return "No PubMed ID available"
    pubmed_link.short_description = 'PubMed'
    
    def mark_as_open_access(self, request, queryset):
        queryset.update(is_open_access=True, paywalled=False)
        self.message_user(request, f'{queryset.count()} papers marked as Open Access.')
    mark_as_open_access.short_description = "Mark selected papers as Open Access"
    
    def mark_as_paywalled(self, request, queryset):
        queryset.update(is_open_access=False, paywalled=True)
        self.message_user(request, f'{queryset.count()} papers marked as Paywalled.')
    mark_as_paywalled.short_description = "Mark selected papers as Paywalled"
    
    def fetch_citations(self, request, queryset):
        # This would trigger citation fetching for selected papers
        count = queryset.count()
        self.message_user(request, f'Citation fetching queued for {count} papers.')
    fetch_citations.short_description = "Fetch citations for selected papers"


@admin.register(CitingPaper)
class CitingPaperAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'authors', 'journal', 'created_at']
    list_filter = ['journal', 'created_at']
    search_fields = ['title', 'authors', 'journal', 'doi']
    readonly_fields = ['created_at', 'updated_at']
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = [
        'citing_paper_short',
        'retracted_paper_short',
        'days_after_retraction',
        'is_post_retraction',
        'source_api',
        'created_at'
    ]
    
    list_filter = [
        'source_api',
        'is_self_citation',
        'created_at',
    ]
    
    search_fields = [
        'citing_paper__title',
        'retracted_paper__title',
        'citing_paper__doi',
        'retracted_paper__record_id'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def citing_paper_short(self, obj):
        return obj.citing_paper.title[:40] + '...' if len(obj.citing_paper.title) > 40 else obj.citing_paper.title
    citing_paper_short.short_description = 'Citing Paper'
    
    def retracted_paper_short(self, obj):
        return obj.retracted_paper.title[:40] + '...' if len(obj.retracted_paper.title) > 40 else obj.retracted_paper.title
    retracted_paper_short.short_description = 'Retracted Paper'
    
    def is_post_retraction(self, obj):
        if obj.days_after_retraction > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Post ({} days)</span>',
                obj.days_after_retraction
            )
        elif obj.days_after_retraction == 0:
            return format_html('<span style="color: orange;">⚠️ Same day</span>')
        else:
            return format_html('<span style="color: green;">✓ Pre-retraction</span>')
    is_post_retraction.short_description = 'Citation Timing'


@admin.register(DataImportLog)
class DataImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'import_type',
        'start_time',
        'end_time',
        'status',
        'records_processed',
        'records_created',
        'records_updated',
        'records_failed',
        'duration'
    ]
    
    list_filter = [
        'import_type',
        'status',
        'start_time',
    ]
    
    readonly_fields = [
        'start_time',
        'end_time',
        'duration',
        'import_type',
        'records_processed',
        'records_created',
        'records_updated',
        'records_failed',
        'status',
        'error_message'
    ]
    
    def duration(self, obj):
        if obj.end_time and obj.start_time:
            duration = obj.end_time - obj.start_time
            return str(duration).split('.')[0]  # Remove microseconds
        return "In progress..." if obj.start_time and not obj.end_time else "N/A"
    duration.short_description = 'Duration'


# Custom admin site title and header
admin.site.site_title = "Citing Retracted Papers Database"
admin.site.site_header = "Citing Retracted Papers Administration"
admin.site.index_title = "Database Administration"
