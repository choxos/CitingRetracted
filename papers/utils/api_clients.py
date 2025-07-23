import requests
import time
import json
import logging
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


class APIRateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.config = settings.API_RATE_LIMITS.get(api_name, {})
        self.requests_per_second = self.config.get('requests_per_second', 1)
        self.min_interval = 1.0 / self.requests_per_second
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()


class OpenAlexAPI:
    """Client for OpenAlex API"""
    
    def __init__(self):
        self.base_url = settings.OPENALEX_BASE_URL
        self.rate_limiter = APIRateLimiter('openalex')
        self.session = requests.Session()
        # Set User-Agent as recommended by OpenAlex
        self.session.headers.update({
            'User-Agent': 'CitingRetracted/1.0 (https://github.com/yourrepo; mailto:your@email.com)'
        })
    
    def search_works_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Search for a work by its DOI"""
        self.rate_limiter.wait_if_needed()
        
        # Clean DOI
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        
        url = f"{self.base_url}/works"
        params = {
            'filter': f'doi:{clean_doi}',
            'per-page': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                return data['results'][0]
            return None
            
        except Exception as e:
            logger.error(f"Error searching OpenAlex for DOI {doi}: {str(e)}")
            return None
    
    def get_citations_for_work(self, openalex_id: str, per_page: int = 200) -> List[Dict[str, Any]]:
        """Get all papers that cite a specific work"""
        self.rate_limiter.wait_if_needed()
        
        # Extract ID from full OpenAlex URL if necessary
        if openalex_id.startswith('https://openalex.org/'):
            work_id = openalex_id.split('/')[-1]
        else:
            work_id = openalex_id
        
        url = f"{self.base_url}/works"
        params = {
            'filter': f'cites:{work_id}',
            'per-page': per_page,
            'cursor': '*'
        }
        
        citing_papers = []
        page = 1
        
        while True:
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                citing_papers.extend(results)
                logger.info(f"Retrieved {len(results)} citing papers (page {page})")
                
                # Check if there's a next page
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                params['cursor'] = next_cursor
                page += 1
                
                # Add delay between pages
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error getting citations from OpenAlex: {str(e)}")
                break
        
        return citing_papers
    
    def parse_work_data(self, work_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAlex work data into our format"""
        publication_date = None
        publication_year = work_data.get('publication_year')
        
        if work_data.get('publication_date'):
            try:
                from datetime import datetime
                publication_date = datetime.strptime(work_data['publication_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Extract journal/venue information
        journal = None
        publisher = None
        primary_location = work_data.get('primary_location', {})
        if primary_location and primary_location.get('source'):
            journal = primary_location['source'].get('display_name')
            publisher = primary_location['source'].get('host_organization_name')
        
        return {
            'openalex_id': work_data.get('id', ''),
            'doi': work_data.get('doi', '').replace('https://doi.org/', '') if work_data.get('doi') else None,
            'title': work_data.get('title', ''),
            'authors': json.dumps(work_data.get('authorships', [])),
            'journal': journal,
            'publisher': publisher,
            'publication_date': publication_date,
            'publication_year': publication_year,
            'cited_by_count': work_data.get('cited_by_count', 0),
            'is_open_access': work_data.get('open_access', {}).get('is_oa', False),
            'concepts': json.dumps(work_data.get('concepts', [])),
            'abstract_inverted_index': json.dumps(work_data.get('abstract_inverted_index', {})),
            'source_api': 'openalex'
        }


class SemanticScholarAPI:
    """Client for Semantic Scholar API"""
    
    def __init__(self):
        self.base_url = settings.SEMANTIC_SCHOLAR_BASE_URL
        self.rate_limiter = APIRateLimiter('semantic_scholar')
        self.session = requests.Session()
    
    def search_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Search for a paper by its DOI"""
        self.rate_limiter.wait_if_needed()
        
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        url = f"{self.base_url}/paper/DOI:{clean_doi}"
        
        params = {
            'fields': 'paperId,title,authors,journal,year,citationCount,isOpenAccess,fieldsOfStudy'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar for DOI {doi}: {str(e)}")
            return None
    
    def get_citations_for_paper(self, paper_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get citations for a paper"""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/paper/{paper_id}/citations"
        params = {
            'fields': 'paperId,title,authors,journal,year,citationCount,isOpenAccess',
            'limit': min(limit, 1000)  # API limit
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error getting citations from Semantic Scholar: {str(e)}")
            return []


class OpenCitationsAPI:
    """Client for OpenCitations API"""
    
    def __init__(self):
        self.base_url = settings.OPENCITATIONS_BASE_URL
        self.rate_limiter = APIRateLimiter('opencitations')
        self.session = requests.Session()
    
    def get_citations_for_doi(self, doi: str) -> List[Dict[str, Any]]:
        """Get citations for a DOI"""
        self.rate_limiter.wait_if_needed()
        
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        url = f"{self.base_url}/citations/{clean_doi}"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting citations from OpenCitations: {str(e)}")
            return []


class CitationRetriever:
    """Main class for retrieving citations using multiple APIs"""
    
    def __init__(self):
        self.openalex = OpenAlexAPI()
        self.semantic_scholar = SemanticScholarAPI()
        self.opencitations = OpenCitationsAPI()
    
    def get_citations_for_paper(self, retracted_paper, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get citations for a retracted paper using multiple APIs"""
        cache_key = f"citations_{retracted_paper.record_id}"
        
        if use_cache:
            cached_citations = cache.get(cache_key)
            if cached_citations:
                return cached_citations
        
        all_citations = []
        
        # Try OpenAlex first (most comprehensive)
        if retracted_paper.original_paper_doi:
            logger.info(f"Searching OpenAlex for citations of {retracted_paper.original_paper_doi}")
            work_data = self.openalex.search_works_by_doi(retracted_paper.original_paper_doi)
            if work_data:
                openalex_id = work_data.get('id')
                citations = self.openalex.get_citations_for_work(openalex_id)
                all_citations.extend(citations)
                logger.info(f"Found {len(citations)} citations in OpenAlex")
        
        # If we don't have enough citations, try Semantic Scholar
        if len(all_citations) < 10 and retracted_paper.original_paper_doi:
            logger.info(f"Searching Semantic Scholar for additional citations")
            paper_data = self.semantic_scholar.search_paper_by_doi(retracted_paper.original_paper_doi)
            if paper_data:
                paper_id = paper_data.get('paperId')
                citations = self.semantic_scholar.get_citations_for_paper(paper_id)
                # Convert to OpenAlex-like format for consistency
                converted_citations = []
                for citation in citations:
                    if citation.get('citingPaper'):
                        converted_citations.append(citation['citingPaper'])
                all_citations.extend(converted_citations)
                logger.info(f"Found {len(converted_citations)} additional citations in Semantic Scholar")
        
        # Cache results for 24 hours
        if use_cache and all_citations:
            cache.set(cache_key, all_citations, 60 * 60 * 24)
        
        return all_citations 