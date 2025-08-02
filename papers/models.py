from django.db import models
from django.urls import reverse
from django.utils import timezone
import json


class RetractedPaper(models.Model):
    """Model for retracted papers from Retraction Watch Database"""
    
    # Basic identifiers
    record_id = models.CharField(max_length=50, unique=True, help_text="Retraction Watch unique identifier")
    title = models.TextField(help_text="Title of the retracted paper")
    
    # DOI and URL information
    original_paper_doi = models.CharField(max_length=255, blank=True, null=True, help_text="DOI of the original paper")
    original_paper_doi_url = models.URLField(blank=True, null=True, help_text="URL to the original paper")
    retraction_doi = models.CharField(max_length=255, blank=True, null=True, help_text="DOI of the retraction notice")
    retraction_doi_url = models.URLField(blank=True, null=True, help_text="URL to the retraction notice")
    
    # Journal information
    journal = models.CharField(max_length=500, blank=True, null=True, help_text="Journal name")
    publisher = models.CharField(max_length=300, blank=True, null=True, help_text="Publisher name")
    
    # Authors
    author = models.TextField(blank=True, null=True, help_text="Author names")
    
    # Dates
    original_paper_date = models.DateField(blank=True, null=True, help_text="Publication date of original paper")
    retraction_date = models.DateField(blank=True, null=True, help_text="Date of retraction")
    
    # Retraction details
    retraction_nature = models.CharField(max_length=500, blank=True, null=True, help_text="Nature of retraction")
    reason = models.TextField(blank=True, null=True, help_text="Reason for retraction")
    
    # Additional metadata
    paywalled = models.BooleanField(default=False, help_text="Whether the paper is behind a paywall")
    is_open_access = models.BooleanField(default=False, help_text="Whether the paper is open access")
    subject = models.CharField(max_length=500, blank=True, null=True, help_text="Subject area")
    broad_subjects = models.TextField(blank=True, null=True, help_text="Semicolon-separated broad subject categories")
    specific_fields = models.TextField(blank=True, null=True, help_text="Semicolon-separated specific fields")
    institution = models.TextField(blank=True, null=True, help_text="Author institution(s)")
    country = models.CharField(max_length=200, blank=True, null=True, help_text="Country of origin")
    article_type = models.CharField(max_length=200, blank=True, null=True, help_text="Type of article")
    urls = models.TextField(blank=True, null=True, help_text="Additional URLs")
    
    # PubMed IDs
    original_paper_pubmed_id = models.CharField(max_length=20, blank=True, null=True, help_text="PubMed ID of original paper")
    retraction_pubmed_id = models.CharField(max_length=20, blank=True, null=True, help_text="PubMed ID of retraction notice")
    
    # Abstract and notes
    abstract = models.TextField(blank=True, null=True, help_text="Paper abstract")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    
    # Citation tracking
    citation_count = models.PositiveIntegerField(default=0, help_text="Number of citations found")
    last_citation_check = models.DateTimeField(blank=True, null=True, help_text="Last time citations were checked")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'retracted_papers'
        ordering = ['-retraction_date']
        indexes = [
            models.Index(fields=['record_id']),
            models.Index(fields=['original_paper_doi']),
            models.Index(fields=['original_paper_pubmed_id']),
            models.Index(fields=['retraction_date']),
            models.Index(fields=['original_paper_date']),               # For analytics queries
            models.Index(fields=['journal']),
            models.Index(fields=['subject']),
            models.Index(fields=['citation_count']),                   # For sorting by citations
            models.Index(fields=['retraction_date', 'citation_count']), # Composite for analytics
            models.Index(fields=['retraction_nature']),                 # For nature-based filtering
        ]
    
    @classmethod
    def get_unique_papers_count(cls):
        """Get count of unique papers (by DOI only)"""
        from django.db.models import Q, Count
        
        # Create a query that groups by DOI only
        unique_papers = cls.objects.exclude(
            Q(original_paper_doi__isnull=True) | Q(original_paper_doi__exact='')
        ).values('original_paper_doi').distinct().count()
        
        # Add papers without DOI (counted individually)
        papers_without_doi = cls.objects.filter(
            Q(original_paper_doi__isnull=True) | Q(original_paper_doi__exact='')
        ).count()
        
        return unique_papers + papers_without_doi
    
    @classmethod
    def get_unique_papers_by_nature(cls):
        """Get count of unique papers grouped by retraction nature (DOI-based only)"""
        from django.db.models import Q, Count
        from django.db.models.functions import Lower
        
        # Group by nature and unique DOI identifiers
        nature_counts = {}
        
        # Get all papers and group them by their DOI
        seen_dois = set()
        
        for paper in cls.objects.all():
            # Create a unique identifier for this paper (DOI only)
            identifier = None
            if paper.original_paper_doi and paper.original_paper_doi.strip():
                identifier = f"doi:{paper.original_paper_doi.strip()}"
            else:
                identifier = f"record:{paper.record_id}"  # Fallback to record ID for papers without DOI
            
            # Only count if we haven't seen this DOI before
            if identifier not in seen_dois:
                seen_dois.add(identifier)
                
                # Categorize the nature
                nature = paper.retraction_nature_display.lower() if paper.retraction_nature else 'retracted'
                
                if 'expression of concern' in nature:
                    category = 'Expression of Concern'
                elif 'correction' in nature or 'corrigendum' in nature:
                    category = 'Correction'
                elif 'reinstatement' in nature:
                    category = 'Reinstatement'
                else:
                    category = 'Retraction'
                
                nature_counts[category] = nature_counts.get(category, 0) + 1
        
        return nature_counts
    
    def __str__(self):
        return f"{self.title[:100]}..." if len(self.title) > 100 else self.title
    
    def get_absolute_url(self):
        return reverse('papers:detail', kwargs={'record_id': self.record_id})
    
    @property
    def original_paper_url(self):
        """Generate URL to original paper"""
        if self.original_paper_doi:
            return f"https://doi.org/{self.original_paper_doi}"
        return None
    
    @property
    def retraction_notice_url(self):
        """Generate URL to retraction notice"""
        if self.retraction_doi:
            return f"https://doi.org/{self.retraction_doi}"
        return None
    
    @property
    def pubmed_url(self):
        """Generate URL to PubMed entry"""
        if self.original_paper_pubmed_id:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.original_paper_pubmed_id}/"
        return None
    
    @property
    def retraction_pubmed_url(self):
        """Generate URL to retraction PubMed entry"""
        if self.retraction_pubmed_id:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.retraction_pubmed_id}/"
        return None
    
    @property
    def access_status(self):
        """Return human-readable access status"""
        if self.is_open_access:
            return "Open Access"
        elif self.paywalled:
            return "Paywalled"
        else:
            return "Unknown"
    
    @property
    def retraction_nature_display(self):
        """Return cleaned retraction nature for display"""
        if self.retraction_nature:
            return self.retraction_nature.strip()
        return "Retracted"
    
    @property
    def retraction_badge_class(self):
        """Return appropriate CSS class based on retraction nature"""
        nature = self.retraction_nature_display.lower()
        if 'expression of concern' in nature:
            return 'retraction-badge-warning'
        elif 'correction' in nature:
            return 'retraction-badge-info'
        elif 'reinstatement' in nature:
            return 'retraction-badge-success'
        else:  # Retraction or default
            return 'retraction-badge'
    
    @property
    def related_records(self):
        """Find other records with the same DOI (DOI-only matching)"""
        related = []
        
        # Find by DOI only
        if self.original_paper_doi and self.original_paper_doi.strip():
            doi_matches = RetractedPaper.objects.filter(
                original_paper_doi=self.original_paper_doi.strip()
            ).exclude(id=self.id)
            related.extend(doi_matches)
        
        return related
    
    @property
    def has_related_records(self):
        """Check if this paper has related records"""
        return len(self.related_records) > 0
    
    @property
    def years_since_retraction(self):
        """Calculate years since retraction with user-friendly display"""
        if self.retraction_date:
            from datetime import date
            today = date.today()
            delta = today - self.retraction_date
            years = delta.days / 365.25
            
            if years < 1:
                return "<1 year"
            elif years < 2:
                return f"{round(years, 1)} year"
            else:
                return f"{round(years, 1)} years"
        return "Unknown"
    
    @property
    def days_since_retraction(self):
        """Calculate days since retraction"""
        if self.retraction_date:
            from datetime import date
            today = date.today()
            return (today - self.retraction_date).days
        return None
    
    @property
    def reason_list(self):
        """Parse multiple retraction reasons separated by semicolons"""
        if not self.reason:
            return []
        
        # Split by semicolon and clean up each reason
        reasons = [reason.strip() for reason in self.reason.split(';') if reason.strip()]
        
        # Clean up common prefixes and formatting
        cleaned_reasons = []
        for reason in reasons:
            # Remove leading + signs
            if reason.startswith('+'):
                reason = reason[1:].strip()
            # Capitalize first letter if not already capitalized
            if reason and not reason[0].isupper():
                reason = reason[0].upper() + reason[1:]
            if reason:
                cleaned_reasons.append(reason)
        
        return cleaned_reasons
    
    @property
    def formatted_reasons(self):
        """Get a nicely formatted string of retraction reasons"""
        reasons = self.reason_list
        if not reasons:
            return ""
        
        if len(reasons) == 1:
            return reasons[0]
        elif len(reasons) == 2:
            return f"{reasons[0]} and {reasons[1]}"
        else:
            return f"{', '.join(reasons[:-1])}, and {reasons[-1]}"
    
    @property
    def individual_reasons(self):
        """Get list of individual retraction reasons for badge display"""
        return self.reason_list
    
    @property
    def author_list(self):
        """Parse multiple authors separated by semicolons"""
        if not self.author:
            return []
        
        # Split by semicolon and clean up each author name
        authors = [author.strip() for author in self.author.split(';') if author.strip()]
        
        # Filter out very short names and clean up
        cleaned_authors = []
        for author in authors:
            if author and len(author) > 2:  # Filter out very short names
                cleaned_authors.append(author)
        
        return cleaned_authors
    
    @property
    def country_list(self):
        """Parse multiple countries separated by semicolons"""
        if not self.country:
            return []
        
        # Split by semicolon and clean up each country
        countries = [country.strip() for country in self.country.split(';') if country.strip()]
        
        # Filter out invalid entries
        invalid_entries = {'', 'Unknown', 'unknown', 'N/A', 'n/a', 'None', 'null', 'NA'}
        cleaned_countries = []
        for country in countries:
            if country and country not in invalid_entries and len(country) > 1:
                cleaned_countries.append(country)
        
        return cleaned_countries
    
    @property
    def institution_list(self):
        """Parse multiple institutions separated by semicolons"""
        if not self.institution:
            return []
        
        # Split by semicolon and clean up each institution
        institutions = [inst.strip() for inst in self.institution.split(';') if inst.strip()]
        
        # Filter out invalid entries
        invalid_entries = {
            '', 'Unknown', 'unknown', 'N/A', 'n/a', 'None', 'null', 'NA',
            'unavailable', 'Unavailable', 'not available', 'Not Available'
        }
        cleaned_institutions = []
        for institution in institutions:
            if institution and institution not in invalid_entries and len(institution) > 2:
                cleaned_institutions.append(institution)
        
        return cleaned_institutions
    
    @property
    def primary_country(self):
        """Get the first/primary country from the country list"""
        countries = self.country_list
        return countries[0] if countries else ''
    
    @property
    def primary_institution(self):
        """Get the first/primary institution from the institution list"""
        institutions = self.institution_list
        return institutions[0] if institutions else ''

    @property
    def subject_list(self):
        """Parse multiple subjects separated by semicolons"""
        if not self.subject:
            return []
        
        # Split by semicolon and clean up each subject
        subjects = [subject.strip() for subject in self.subject.split(';') if subject.strip()]
        return subjects
    
    @property
    def parsed_subjects(self):
        """Parse subjects into broad categories and specific fields"""
        if not self.subject:
            return []
        
        parsed = []
        subjects = [subject.strip() for subject in self.subject.split(';') if subject.strip()]
        
        for subject in subjects:
            # Handle format: (ABBR) Field Name
            if subject.startswith('(') and ')' in subject:
                # Extract abbreviation and expand it
                end_paren = subject.find(')')
                abbr = subject[1:end_paren].strip()
                field = subject[end_paren + 1:].strip()
                
                # Map abbreviations to full names
                broad_category = self._expand_subject_abbreviation(abbr)
                parsed.append({
                    'broad_category': broad_category,
                    'broad_abbr': abbr,
                    'specific_field': field,
                    'full_text': subject
                })
            # Handle format: Broad Category - Specific Field
            elif ' - ' in subject:
                parts = subject.split(' - ', 1)
                broad_category = parts[0].strip()
                specific_field = parts[1].strip()
                parsed.append({
                    'broad_category': broad_category,
                    'broad_abbr': self._get_subject_abbreviation(broad_category),
                    'specific_field': specific_field,
                    'full_text': subject
                })
            # Handle single category
            else:
                parsed.append({
                    'broad_category': subject,
                    'broad_abbr': self._get_subject_abbreviation(subject),
                    'specific_field': None,
                    'full_text': subject
                })
        
        return parsed
    
    def _expand_subject_abbreviation(self, abbr):
        """Expand subject abbreviations to full names"""
        abbreviation_map = {
            'HSC': 'Health Sciences',
            'BLS': 'Biological and Life Sciences',
            'PSE': 'Physical Sciences and Engineering',
            'SSH': 'Social Sciences and Humanities',
            'CS': 'Computer Science',
            'MATH': 'Mathematics',
            'ENVS': 'Environmental Sciences',
            'AGRI': 'Agriculture',
            'EDU': 'Education',
            'BUS': 'Business',
            'LAW': 'Law',
            'ART': 'Arts',
            'MED': 'Medicine',
            'BIO': 'Biology',
            'CHEM': 'Chemistry',
            'PHYS': 'Physics',
            'PSYCH': 'Psychology',
            'SOC': 'Sociology',
        }
        return abbreviation_map.get(abbr.upper(), abbr)
    
    def _get_subject_abbreviation(self, broad_category):
        """Get abbreviation for broad category"""
        category_abbr_map = {
            'Health Sciences': 'HSC',
            'Medicine': 'HSC',
            'Biology': 'BLS',
            'Biochemistry': 'BLS',
            'Chemistry': 'PSE',
            'Physics': 'PSE',
            'Engineering': 'PSE',
            'Computer Science': 'CS',
            'Mathematics': 'MATH',
            'Psychology': 'SSH',
            'Sociology': 'SSH',
            'Public Health and Safety': 'HSC',
            'Environmental Science': 'ENVS',
            'Agriculture': 'AGRI',
            'Business': 'BUS',
            'Education': 'EDU',
            'Arts': 'ART',
        }
        return category_abbr_map.get(broad_category, broad_category[:3].upper())
    
    @property
    def broad_subject_categories(self):
        """Get unique broad subject categories"""
        parsed = self.parsed_subjects
        return list(set([s['broad_category'] for s in parsed if s['broad_category']]))
    
    @property
    def formatted_subjects_with_broad(self):
        """Get formatted string showing broad categories and specific fields"""
        parsed = self.parsed_subjects
        if not parsed:
            return ""
        
        formatted = []
        for subject in parsed:
            if subject['specific_field']:
                formatted.append(f"{subject['broad_category']} - {subject['specific_field']}")
            else:
                formatted.append(subject['broad_category'])
        
        return "; ".join(formatted)
    
    @property
    def formatted_subjects(self):
        """Get a nicely formatted string of subjects"""
        subjects = self.subject_list
        if not subjects:
            return ""
        
        return ", ".join(subjects)
    
    @property
    def is_recent_retraction(self):
        if self.retraction_date:
            return (timezone.now().date() - self.retraction_date).days <= 365
        return False
    
    @property
    def original_paper_url(self):
        """Generate URL to original paper if DOI is available."""
        if self.original_paper_doi:
            return f"https://doi.org/{self.original_paper_doi}"
        return None
    
    @property
    def retraction_notice_url(self):
        """Generate URL to retraction notice if DOI is available."""
        if self.retraction_doi:
            return f"https://doi.org/{self.retraction_doi}"
        return None
    
    @property
    def pubmed_url(self):
        """Generate PubMed URL if PMID is available."""
        if self.original_paper_pubmed_id and self.original_paper_pubmed_id != '0':
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.original_paper_pubmed_id}/"
        return None
    
    @property
    def retraction_pubmed_url(self):
        """Generate PubMed URL for retraction notice if PMID is available."""
        if self.retraction_pubmed_id and self.retraction_pubmed_id != '0':
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.retraction_pubmed_id}/"
        return None
    
    @property
    def primary_country(self):
        """Extract primary country from country field."""
        if self.country:
            # Handle multiple countries separated by semicolons
            countries = [c.strip() for c in self.country.split(';')]
            return countries[0] if countries else ''
        return ''
    
    @property
    def primary_subject(self):
        """Extract primary subject from subject field."""
        if self.subject:
            # Handle multiple subjects separated by semicolons
            subjects = [s.strip() for s in self.subject.split(';')]
            # Remove prefix codes like (PHY), (B/T) etc.
            if subjects:
                subject = subjects[0]
                if ')' in subject:
                    subject = subject.split(')', 1)[1].strip()
                return subject
        return ''


class CitingPaper(models.Model):
    """Model for papers that cite retracted papers"""
    
    # Basic identifiers
    openalex_id = models.CharField(max_length=255, unique=True, help_text="OpenAlex unique identifier")
    doi = models.CharField(max_length=255, blank=True, null=True, help_text="DOI of the citing paper")
    title = models.TextField(help_text="Title of the citing paper")
    
    # Authors and journal
    authors = models.TextField(blank=True, null=True, help_text="Author names (JSON format)")
    journal = models.CharField(max_length=500, blank=True, null=True, help_text="Journal name")
    publisher = models.CharField(max_length=300, blank=True, null=True, help_text="Publisher name")
    
    # Publication details
    publication_date = models.DateField(blank=True, null=True, help_text="Publication date")
    publication_year = models.PositiveIntegerField(blank=True, null=True, help_text="Publication year")
    
    # Citation context
    cited_by_count = models.PositiveIntegerField(default=0, help_text="Number of citations this paper has")
    is_open_access = models.BooleanField(default=False, help_text="Whether the paper is open access")
    
    # Metadata from OpenAlex
    concepts = models.TextField(blank=True, null=True, help_text="Research concepts (JSON format)")
    mesh_terms = models.TextField(blank=True, null=True, help_text="MeSH terms (JSON format)")
    abstract_inverted_index = models.TextField(blank=True, null=True, help_text="Abstract inverted index (JSON format)")
    
    # Source information
    source_api = models.CharField(max_length=50, default='openalex', help_text="API source (openalex, semantic_scholar, etc.)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citing_papers'
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['openalex_id']),
            models.Index(fields=['doi']),
            models.Index(fields=['publication_date']),
            models.Index(fields=['publication_year']),
        ]
    
    def __str__(self):
        return f"{self.title[:100]}..." if len(self.title) > 100 else self.title
    
    @property
    def authors_list(self):
        """Parse authors JSON into a list"""
        if self.authors:
            try:
                # If it's already a list/dict (from raw storage), return it
                if isinstance(self.authors, (list, dict)):
                    return self.authors if isinstance(self.authors, list) else [self.authors]
                # Try to parse JSON string
                return json.loads(self.authors)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @property
    def formatted_authors(self):
        """Get a clean, formatted string of author names"""
        authors = self.authors_list
        if not authors:
            return "Unknown Authors"
        
        author_names = []
        for author in authors[:3]:  # Limit to first 3 authors
            if isinstance(author, dict):
                # Handle OpenAlex format: {'author': {'display_name': 'Name'}}
                if 'author' in author and isinstance(author['author'], dict):
                    name = author['author'].get('display_name', '')
                # Handle direct format: {'display_name': 'Name'}
                elif 'display_name' in author:
                    name = author['display_name']
                # Handle raw name strings
                elif 'raw_author_name' in author:
                    name = author['raw_author_name']
                else:
                    name = str(author).split(',')[0]  # Fallback: take first part
                
                if name:
                    author_names.append(name.strip())
            elif isinstance(author, str):
                author_names.append(author.strip())
        
        if not author_names:
            return "Unknown Authors"
        
        result = ", ".join(author_names)
        if len(authors) > 3:
            result += f" et al. ({len(authors)} authors)"
        
        return result
    
    @property
    def concepts_list(self):
        """Parse concepts JSON into a list"""
        if self.concepts:
            try:
                return json.loads(self.concepts)
            except json.JSONDecodeError:
                return []
        return []


class Citation(models.Model):
    """Model linking retracted papers to papers that cite them"""
    
    retracted_paper = models.ForeignKey(
        RetractedPaper, 
        on_delete=models.CASCADE, 
        related_name='citations',
        help_text="The retracted paper being cited"
    )
    citing_paper = models.ForeignKey(
        CitingPaper, 
        on_delete=models.CASCADE, 
        related_name='retracted_citations',
        help_text="The paper that cites the retracted paper"
    )
    
    # Citation context
    citation_date = models.DateField(blank=True, null=True, help_text="Date when citation was made")
    days_after_retraction = models.IntegerField(blank=True, null=True, help_text="Days between retraction and citation")
    
    # Additional metadata
    citation_context = models.TextField(blank=True, null=True, help_text="Context in which the citation appears")
    is_self_citation = models.BooleanField(default=False, help_text="Whether this is a self-citation")
    
    # Data source and validation
    source_api = models.CharField(max_length=50, default='openalex', help_text="API source for this citation")
    confidence_score = models.FloatField(blank=True, null=True, help_text="Confidence score for the citation match")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citations'
        unique_together = ['retracted_paper', 'citing_paper']
        ordering = ['-citation_date']
        indexes = [
            models.Index(fields=['citation_date']),
            models.Index(fields=['days_after_retraction']),
            models.Index(fields=['retracted_paper', 'days_after_retraction']),  # Composite for analytics
            models.Index(fields=['citing_paper', 'days_after_retraction']),     # Composite for analytics
            models.Index(fields=['created_at']),                                # For recent data queries
            models.Index(fields=['retracted_paper', 'created_at']),             # Composite for paper-specific queries
        ]
    
    def __str__(self):
        return f"Citation: {self.citing_paper.title[:50]}... → {self.retracted_paper.title[:50]}..."
    
    @property
    def citation_type_display(self):
        """Return citation type based on the retracted paper's nature"""
        if self.days_after_retraction is None:
            return "Unknown timing"
        
        if self.days_after_retraction < 0:
            return "Pre-notice"
        elif self.days_after_retraction == 0:
            return "Same day"
        else:  # Post-notice citation
            nature = self.retracted_paper.retraction_nature_display.lower()
            if 'expression of concern' in nature:
                return "Post-expression of concern"
            elif 'correction' in nature:
                return "Post-correction"
            elif 'reinstatement' in nature:
                return "Post-reinstatement"
            else:  # Retraction or default
                return "Post-retraction"
    
    @property
    def citation_badge_class(self):
        """Return appropriate CSS class based on citation type"""
        if self.days_after_retraction is None:
            return 'badge bg-secondary'
        
        if self.days_after_retraction < 0:
            return 'xera-badge xera-badge-success'
        elif self.days_after_retraction == 0:
            return 'xera-badge xera-badge-warning'
        else:  # Post-notice citation
            nature = self.retracted_paper.retraction_nature_display.lower()
            if 'expression of concern' in nature:
                return 'prct-retraction-badge retraction-badge-warning'
            elif 'correction' in nature:
                return 'prct-retraction-badge retraction-badge-info'
            elif 'reinstatement' in nature:
                return 'prct-retraction-badge retraction-badge-success'
            else:  # Retraction or default
                return 'prct-retraction-badge retraction-badge'
    
    def save(self, *args, **kwargs):
        # Calculate days after retraction if both dates are available
        if (self.retracted_paper.retraction_date and 
            self.citing_paper and
            self.citing_paper.publication_date):
            
            # Calculate days (can be negative for pre-retraction citations)
            self.days_after_retraction = (
                self.citing_paper.publication_date - self.retracted_paper.retraction_date
            ).days
        else:
            self.days_after_retraction = None
            
        super().save(*args, **kwargs)
        
        # Update citation count on retracted paper
        self.retracted_paper.citation_count = self.retracted_paper.citations.count()
        self.retracted_paper.save(update_fields=['citation_count'])


class DataImportLog(models.Model):
    """Model to track data import operations"""
    
    IMPORT_TYPES = [
        ('retraction_watch', 'Retraction Watch CSV'),
        ('openalex', 'OpenAlex API'),
        ('semantic_scholar', 'Semantic Scholar API'),
        ('opencitations', 'OpenCitations API'),
    ]
    
    import_type = models.CharField(max_length=50, choices=IMPORT_TYPES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    
    # Statistics
    records_processed = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    
    # Status and errors
    status = models.CharField(max_length=20, default='running')  # running, completed, failed
    error_message = models.TextField(blank=True, null=True)
    error_details = models.TextField(blank=True, null=True)
    
    # Additional metadata
    file_path = models.CharField(max_length=500, blank=True, null=True)
    api_endpoint = models.URLField(blank=True, null=True)
    parameters = models.TextField(blank=True, null=True, help_text="Import parameters (JSON format)")
    
    class Meta:
        db_table = 'data_import_logs'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.import_type} import - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None
