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
            models.Index(fields=['retraction_date']),
            models.Index(fields=['journal']),
            models.Index(fields=['subject']),
        ]
    
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
    def subject_list(self):
        """Parse multiple subjects separated by semicolons"""
        if not self.subject:
            return []
        
        # Split by semicolon and clean up each subject
        subjects = [subject.strip() for subject in self.subject.split(';') if subject.strip()]
        return subjects
    
    @property
    def formatted_subjects(self):
        """Get a nicely formatted string of subjects"""
        subjects = self.subject_list
        if not subjects:
            return ""
        
        return ", ".join(subjects)
    
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
    
    @property
    def access_status(self):
        """Return human-readable access status."""
        if self.is_open_access:
            return "Open Access"
        elif self.is_paywalled:
            return "Paywalled"
        else:
            return "Unknown"
    

    
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
    
    @property
    def access_status(self):
        """Return human-readable access status."""
        if self.is_open_access:
            return "Open Access"
        elif self.is_paywalled:
            return "Paywalled"
        else:
            return "Unknown"


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
        ]
    
    def __str__(self):
        return f"Citation: {self.citing_paper.title[:50]}... → {self.retracted_paper.title[:50]}..."
    
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
