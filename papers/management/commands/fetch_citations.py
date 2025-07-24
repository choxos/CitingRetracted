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
    
    def get_citation_count(self, doi: str) -> int:
        """Get citation count for a DOI"""
        try:
            url = f"{self.base_url}/citation-count/{doi}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            count = int(result[0]['count']) if result else 0
            logger.info(f"OpenCitations: {doi} has {count} citations")
            return count
            
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            logger.error(f"OpenCitations citation count error for {doi}: {e}")
            return 0
    
    def get_metadata(self, dois: List[str]) -> List[Dict]:
        """Get metadata for multiple DOIs (bulk operation)"""
        try:
            # OpenCitations supports multiple DOIs separated by __
            dois_param = "__".join(dois[:10])  # Limit to 10 DOIs per request
            url = f"{self.base_url}/metadata/{dois_param}"
            
            response = self.session.get(url, timeout=60)  # Longer timeout for bulk
            response.raise_for_status()
            
            metadata = response.json()
            logger.info(f"OpenCitations: Retrieved metadata for {len(metadata)} papers")
            return metadata
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenCitations metadata error: {e}")
            return []
    
    def parse_timespan(self, timespan_str: str) -> Optional[int]:
        """Parse XSD duration format (P6Y4M4D) to days"""
        if not timespan_str:
            return None
            
        try:
            # Match pattern like P6Y4M4D or P1Y1M0D
            pattern = r'P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?'
            match = re.match(pattern, timespan_str)
            
            if match:
                years = int(match.group(1) or 0)
                months = int(match.group(2) or 0) 
                days = int(match.group(3) or 0)
                
                # Approximate conversion to days
                total_days = (years * 365) + (months * 30) + days
                return total_days
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse timespan '{timespan_str}': {e}")
            
        return None

class HybridCitationFetcher:
    """Hybrid citation fetcher using multiple APIs with OpenCitations as primary"""
    
    def __init__(self):
        # Initialize APIs
        self.opencitations = OpenCitationsAPI()
        self.openalex_available = True
        self.semantic_scholar_available = True
        
        # Rate limiting tracking
        self.last_openalex_call = 0
        self.last_semantic_call = 0
        
    def fetch_citations_for_paper(self, retracted_paper) -> Tuple[int, int]:
        """
        Fetch citations using hybrid approach:
        1. Primary: OpenCitations (unlimited)
        2. Fallback: OpenAlex + Semantic Scholar (rate-limited)
        """
        doi = retracted_paper.original_paper_doi
        if not doi:
            logger.warning(f"No DOI for paper {retracted_paper.id}")
            return 0, 0
        
        # Clean DOI
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        
        # Step 1: Try OpenCitations first (primary source)
        citations_found = 0
        citations_created = 0
        
        try:
            oc_citations = self.opencitations.get_citations(clean_doi)
            
            for citation_data in oc_citations:
                citing_doi = citation_data.get('citing', '').replace('https://doi.org/', '')
                creation_date = citation_data.get('creation')
                timespan = citation_data.get('timespan')
                
                if citing_doi and creation_date:
                    # Parse creation date
                    try:
                        if len(creation_date) == 7:  # YYYY-MM format
                            citation_date = datetime.strptime(creation_date + '-01', '%Y-%m-%d').date()
                        else:  # YYYY-MM-DD format
                            citation_date = datetime.strptime(creation_date, '%Y-%m-%d').date()
                    except ValueError:
                        citation_date = None
                    
                    # Calculate days after retraction
                    days_after_retraction = None
                    if citation_date and retracted_paper.retraction_date:
                        delta = citation_date - retracted_paper.retraction_date
                        days_after_retraction = delta.days
                    
                    # Create or update citing paper
                    citing_paper, created = CitingPaper.objects.get_or_create(
                        doi=citing_doi,
                        defaults={
                            'title': f'Paper citing {retracted_paper.title[:50]}...',
                            'publication_date': citation_date,
                            'source': 'opencitations'
                        }
                    )
                    
                    # Create citation record
                    citation_obj, citation_created = Citation.objects.get_or_create(
                        retracted_paper=retracted_paper,
                        citing_paper=citing_paper,
                        defaults={
                            'citation_date': citation_date,
                            'days_after_retraction': days_after_retraction,
                            'source': 'opencitations',
                            'timespan_original': timespan
                        }
                    )
                    
                    if citation_created:
                        citations_created += 1
                    citations_found += 1
            
            logger.info(f"OpenCitations: {citations_found} citations found, {citations_created} new")
            
        except Exception as e:
            logger.error(f"OpenCitations failed for {doi}: {e}")
        
        # Step 2: Supplement with OpenAlex if available and not rate-limited
        if self.openalex_available and citations_found < 50:  # If low citation count, supplement
            try:
                if time.time() - self.last_openalex_call > 1:  # 1 second rate limit
                    openalex_citations = self._fetch_openalex_citations(retracted_paper)
                    citations_found += openalex_citations[0]
                    citations_created += openalex_citations[1]
                    self.last_openalex_call = time.time()
                    time.sleep(0.1)  # Be polite
                    
            except Exception as e:
                logger.warning(f"OpenAlex supplementary fetch failed: {e}")
                if "429" in str(e) or "rate limit" in str(e).lower():
                    self.openalex_available = False
                    logger.warning("OpenAlex rate limited - disabling for this session")
        
        # Step 3: Final fallback to Semantic Scholar for recent papers
        if (self.semantic_scholar_available and 
            citations_found < 20 and 
            retracted_paper.retraction_date and 
            retracted_paper.retraction_date > datetime.now().date() - timedelta(days=365*3)):
            
            try:
                if time.time() - self.last_semantic_call > 3:  # 3 second rate limit
                    semantic_citations = self._fetch_semantic_scholar_citations(retracted_paper)
                    citations_found += semantic_citations[0]
                    citations_created += semantic_citations[1]
                    self.last_semantic_call = time.time()
                    time.sleep(1)  # Be extra polite
                    
            except Exception as e:
                logger.warning(f"Semantic Scholar supplementary fetch failed: {e}")
                if "429" in str(e) or "rate limit" in str(e).lower():
                    self.semantic_scholar_available = False
        
        return citations_found, citations_created
    
    def _fetch_openalex_citations(self, retracted_paper) -> Tuple[int, int]:
        """Fallback OpenAlex citation fetching"""
        # Implement existing OpenAlex logic here
        return 0, 0
    
    def _fetch_semantic_scholar_citations(self, retracted_paper) -> Tuple[int, int]:
        """Fallback Semantic Scholar citation fetching"""  
        # Implement existing Semantic Scholar logic here
        return 0, 0


class Command(BaseCommand):
    help = 'Fetch citations for retracted papers using hybrid API approach'

    def add_arguments(self, parser):
        parser.add_argument(
            '--paper-id',
            type=int,
            help='Fetch citations for a specific paper ID'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of papers to process (default: 100)'
        )
        parser.add_argument(
            '--source',
            choices=['hybrid', 'opencitations', 'openalex', 'semantic'],
            default='hybrid',
            help='Citation source to use (default: hybrid)'
        )
        parser.add_argument(
            '--opencitations-token',
            type=str,
            help='OpenCitations access token for better performance'
        )

    def handle(self, *args, **options):
        paper_id = options.get('paper_id')
        limit = options.get('limit', 100)
        source = options.get('source', 'hybrid')
        oc_token = options.get('opencitations_token')

        # Initialize fetcher based on source
        if source == 'hybrid':
            fetcher = HybridCitationFetcher()
            if oc_token:
                fetcher.opencitations = OpenCitationsAPI(access_token=oc_token)
        elif source == 'opencitations':
            fetcher = OpenCitationsAPI(access_token=oc_token)
        else:
            # Use existing logic for other sources
            fetcher = CitationRetriever()

        start_time = timezone.now()
        total_papers = 0
        total_citations_found = 0
        total_new_citations = 0

        self.stdout.write(
            self.style.SUCCESS(f'Starting citation fetch using {source} source...')
        )

        try:
            # Query papers
            if paper_id:
                papers = RetractedPaper.objects.filter(id=paper_id)
                if not papers.exists():
                    self.stdout.write(
                        self.style.ERROR(f'No paper found with ID {paper_id}')
                    )
                    return
            else:
                # Process papers with no citations first, then recently retracted
                papers = RetractedPaper.objects.filter(
                    original_paper_doi__isnull=False,
                    original_paper_doi__gt=''
                ).order_by('-retraction_date')[:limit]

            self.stdout.write(f'Processing {papers.count()} papers...')

            for paper in papers:
                try:
                    with transaction.atomic():
                        if source == 'hybrid':
                            citations_found, new_citations = fetcher.fetch_citations_for_paper(paper)
                        elif source == 'opencitations':
                            citations_found, new_citations = self._fetch_opencitations_only(fetcher, paper)
                        else:
                            # Use existing logic
                            citations_found, new_citations = self._fetch_legacy_sources(fetcher, paper)

                        total_papers += 1
                        total_citations_found += citations_found
                        total_new_citations += new_citations

                        self.stdout.write(
                            f'Paper {paper.id}: {citations_found} citations '
                            f'({new_citations} new) - {paper.title[:60]}...'
                        )

                        # Be polite to APIs
                        time.sleep(0.5)

                except Exception as e:
                    logger.error(f'Error processing paper {paper.id}: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'Error processing paper {paper.id}: {e}')
                    )
                    continue

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Citation fetch interrupted by user')
            )
        except Exception as e:
            logger.error(f'Fatal error during citation fetch: {e}')
            self.stdout.write(
                self.style.ERROR(f'Fatal error: {e}')
            )

        # Report results
        duration = timezone.now() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Citation fetch completed!\n'
                f'📄 Papers processed: {total_papers}\n'
                f'📈 Total citations found: {total_citations_found}\n'
                f'✨ New citations added: {total_new_citations}\n'
                f'⏱️ Duration: {duration}\n'
                f'📡 Source: {source}\n'
                f'🚀 Average: {total_citations_found/max(total_papers,1):.1f} citations/paper'
            )
        )

    def _fetch_opencitations_only(self, fetcher, paper):
        """Fetch citations using only OpenCitations"""
        doi = paper.original_paper_doi
        if not doi:
            return 0, 0

        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
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
                        'title': f'Paper citing {paper.title[:50]}...',
                        'publication_date': citation_date,
                        'source': 'opencitations'
                    }
                )

                # Create citation
                citation_obj, citation_created = Citation.objects.get_or_create(
                    retracted_paper=paper,
                    citing_paper=citing_paper,
                    defaults={
                        'citation_date': citation_date,
                        'days_after_retraction': days_after_retraction,
                        'source': 'opencitations'
                    }
                )

                if citation_created:
                    new_citations += 1
                citations_found += 1

        return citations_found, new_citations

    def _fetch_legacy_sources(self, fetcher, paper):
        """Fallback to existing OpenAlex/Semantic Scholar logic"""
        # Implement existing logic here or call existing methods
        return 0, 0 