from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from papers.models import RetractedPaper, CitingPaper, Citation
from papers.utils.api_clients import CitationRetriever, OpenAlexAPI
import logging
import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from django.core.cache import cache


logger = logging.getLogger(__name__)


class OpenCitationsAPI:
    """OpenCitations COCI API client for citation data"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.base_url = "https://opencitations.net/index/coci/api/v1"
        self.session = requests.Session()
        
        # Set headers for polite API usage
        headers = {
            'User-Agent': 'PRCT-CitationTracker/1.0 (contact@yourproject.org)',
            'Accept': 'application/json'
        }
        
        if access_token:
            headers['Authorization'] = access_token
            
        self.session.headers.update(headers)
        
    def get_citations(self, doi: str) -> List[Dict]:
        """Get all citations to a DOI"""
        try:
            url = f"{self.base_url}/citations/{doi}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            citations = response.json()
            logger.info(f"OpenCitations: Found {len(citations)} citations for {doi}")
            return citations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenCitations API error for {doi}: {e}")
            return []


class Command(BaseCommand):
    help = 'Fetch citations for retracted papers with real-time database updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of papers to process in this batch'
        )
        parser.add_argument(
            '--offset',
            type=int,
            default=0,
            help='Number of papers to skip (for pagination)'
        )
        parser.add_argument(
            '--clear-cache-interval',
            type=int,
            default=5,
            help='Clear cache every N papers for real-time updates'
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', 10)
        offset = options.get('offset', 0)
        clear_cache_interval = options.get('clear_cache_interval', 5)

        # Initialize API client
        fetcher = OpenCitationsAPI()

        start_time = timezone.now()
        papers_processed = 0
        total_citations_found = 0
        total_new_citations = 0

        self.stdout.write(
            self.style.SUCCESS(f'Starting real-time citation fetch: batch_size={batch_size}, offset={offset}')
        )

        try:
            # Query papers with valid DOIs, ordered by retraction date
            papers_queryset = RetractedPaper.objects.filter(
                original_paper_doi__isnull=False,
                original_paper_doi__gt=''
            ).exclude(
                original_paper_doi__iexact='unavailable'
            ).exclude(
                original_paper_doi__iexact='none'
            ).exclude(
                original_paper_doi__iexact='null'
            ).order_by('-retraction_date')
            
            # Apply offset and limit for this batch
            papers = papers_queryset[offset:offset + batch_size]

            self.stdout.write(f'Processing {len(papers)} papers (offset {offset})...')

            for i, paper in enumerate(papers):
                paper_start_time = timezone.now()
                
                try:
                    # Process each paper individually with immediate database commit
                    with transaction.atomic():
                        citations_found, new_citations = self._fetch_citations_for_paper(fetcher, paper)
                        
                        papers_processed += 1
                        total_citations_found += citations_found
                        total_new_citations += new_citations
                        
                        # Log progress for each paper
                        paper_duration = timezone.now() - paper_start_time
                        self.stdout.write(
                            f'  Paper {i+1}/{len(papers)}: {paper.record_id} - '
                            f'{citations_found} citations ({new_citations} new) - '
                            f'{paper_duration.total_seconds():.1f}s'
                        )
                        
                        # Clear cache periodically for real-time visibility
                        if papers_processed % clear_cache_interval == 0:
                            self._clear_cache_selective()
                            self.stdout.write(
                                f'  🔄 Cache cleared for real-time updates ({papers_processed} papers processed)'
                            )
                        
                        # Small delay to be polite to APIs
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"Error processing paper {paper.id}: {e}")
                    self.stdout.write(
                        self.style.ERROR(f'  Error processing paper {paper.record_id}: {e}')
                    )
                    continue

            # Final statistics
            duration = timezone.now() - start_time
            
            # Output statistics in a format the auto updater can parse
            self.stdout.write(
                self.style.SUCCESS(
                    f'Real-time citation fetch completed!\n'
                    f'Papers processed: {papers_processed}\n'
                    f'Citations found: {total_citations_found}\n'
                    f'New citations: {total_new_citations}\n'
                    f'Duration: {duration.total_seconds():.1f}s'
                )
            )

        except Exception as e:
            logger.error(f"Real-time citation fetch error: {e}")
            self.stdout.write(
                self.style.ERROR(f'Real-time citation fetch failed: {e}')
            )
            raise

    def _fetch_citations_for_paper(self, fetcher, paper):
        """Fetch citations for a single paper"""
        doi = paper.original_paper_doi
        if not doi or doi.lower() in ['unavailable', 'none', 'null', '']:
            logger.warning(f"No valid DOI for paper {paper.id}: '{doi}'")
            return 0, 0

        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        
        # Validate DOI format
        if not clean_doi.startswith('10.'):
            logger.warning(f"Invalid DOI format for paper {paper.id}: '{clean_doi}'")
            return 0, 0
            
        citations = fetcher.get_citations(clean_doi)
        
        citations_found = 0
        new_citations = 0
        
        for citation_data in citations:
            citing_doi = citation_data.get('citing', '').replace('https://doi.org/', '')
            creation_date = citation_data.get('creation')
            
            if citing_doi and creation_date:
                # Parse date
                try:
                    if len(creation_date) == 7:  # YYYY-MM
                        citation_date = datetime.strptime(creation_date + '-01', '%Y-%m-%d').date()
                    else:  # YYYY-MM-DD
                        citation_date = datetime.strptime(creation_date, '%Y-%m-%d').date()
                except ValueError:
                    citation_date = None

                # Calculate days after retraction
                days_after_retraction = None
                if citation_date and paper.retraction_date:
                    delta = citation_date - paper.retraction_date
                    days_after_retraction = delta.days

                # Create citing paper
                citing_paper, created = CitingPaper.objects.get_or_create(
                    doi=citing_doi,
                    defaults={
                        'openalex_id': f'opencitations_{citing_doi}',
                        'title': f'Paper citing {paper.title[:50]}...',
                        'publication_date': citation_date,
                        'source_api': 'opencitations'
                    }
                )

                # Create citation
                citation_obj, citation_created = Citation.objects.get_or_create(
                    retracted_paper=paper,
                    citing_paper=citing_paper,
                    defaults={
                        'citation_date': citation_date,
                        'days_after_retraction': days_after_retraction,
                        'source_api': 'opencitations'
                    }
                )

                if citation_created:
                    new_citations += 1
                citations_found += 1

        return citations_found, new_citations

    def _clear_cache_selective(self):
        """Clear specific cache keys for real-time updates"""
        cache_keys = [
            'analytics_complex_data_v2',
            'analytics_basic_stats_v2',
            'home_stats_v1',
            'home_sidebar_stats_v1',
            'analytics_overview',
            'citation_analysis'
        ]
        
        for key in cache_keys:
            cache.delete(key) 