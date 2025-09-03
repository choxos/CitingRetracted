#!/usr/bin/env python3
"""
Advanced Journal Website Scraper
Multi-modal data extraction from journal websites
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse
import time
import re
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import logging
from fake_useragent import UserAgent
from textstat import flesch_reading_ease, flesch_kincaid_grade
from langdetect import detect
import whois
import ssl
import socket

from config import Config
from utils.text_analyzer import TextAnalyzer
from utils.domain_analyzer import DomainAnalyzer

class JournalScraper:
    """Advanced journal website scraper with multi-modal analysis"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.ua = UserAgent()
        self.text_analyzer = TextAnalyzer()
        self.domain_analyzer = DomainAnalyzer()
        self.session = requests.Session()
        self.setup_session()
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, self.config.LOG_LEVEL))
        self.logger = logging.getLogger(__name__)
        
        # Selenium setup for dynamic content
        self.setup_selenium()
    
    def setup_session(self):
        """Configure requests session with proper headers and settings"""
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for dynamic content"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.config.USER_AGENT}')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.logger.warning(f"Selenium setup failed: {e}. Dynamic content scraping disabled.")
            self.driver = None
    
    async def scrape_journal(self, journal_url: str) -> Dict:
        """
        Main method to scrape complete journal information
        
        Args:
            journal_url: URL of the journal website
            
        Returns:
            Dictionary containing all scraped journal data
        """
        start_time = time.time()
        self.logger.info(f"Starting scrape for: {journal_url}")
        
        try:
            # Initialize result dictionary
            result = {
                'url': journal_url,
                'scrape_timestamp': datetime.now().isoformat(),
                'scrape_success': False,
                'error_message': None,
                'scrape_duration': 0,
            }
            
            # Basic website analysis
            basic_info = await self.get_basic_website_info(journal_url)
            result.update(basic_info)
            
            if not basic_info.get('accessible', False):
                result['error_message'] = "Website not accessible"
                return result
            
            # Get page content
            content = await self.get_page_content(journal_url)
            result['content'] = content
            
            # Extract journal metadata
            metadata = self.extract_journal_metadata(content['soup'], journal_url)
            result['metadata'] = metadata
            
            # Analyze editorial board
            editorial_info = await self.analyze_editorial_board(content['soup'], journal_url)
            result['editorial_board'] = editorial_info
            
            # Extract submission information
            submission_info = self.extract_submission_info(content['soup'])
            result['submission_info'] = submission_info
            
            # Analyze contact information
            contact_info = self.analyze_contact_info(content['soup'])
            result['contact_info'] = contact_info
            
            # Extract publication fees
            fees_info = self.extract_fees_info(content['soup'])
            result['fees_info'] = fees_info
            
            # Analyze website quality
            quality_metrics = await self.analyze_website_quality(journal_url, content)
            result['quality_metrics'] = quality_metrics
            
            # Content quality analysis
            content_quality = self.analyze_content_quality(content['text'])
            result['content_quality'] = content_quality
            
            # Technical analysis
            technical_analysis = await self.technical_analysis(journal_url)
            result['technical_analysis'] = technical_analysis
            
            result['scrape_success'] = True
            result['scrape_duration'] = time.time() - start_time
            
            self.logger.info(f"Successfully scraped {journal_url} in {result['scrape_duration']:.2f}s")
            
        except Exception as e:
            result['error_message'] = str(e)
            result['scrape_duration'] = time.time() - start_time
            self.logger.error(f"Error scraping {journal_url}: {e}")
        
        return result
    
    async def get_basic_website_info(self, url: str) -> Dict:
        """Get basic website accessibility and response information"""
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            return {
                'accessible': True,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'final_url': response.url,
                'headers': dict(response.headers),
                'has_ssl': url.startswith('https://'),
                'page_size': len(response.content)
            }
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e)
            }
    
    async def get_page_content(self, url: str) -> Dict:
        """Extract page content using both requests and selenium"""
        content = {}
        
        try:
            # Get content with requests
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            content['html'] = str(soup)
            content['text'] = soup.get_text(separator=' ', strip=True)
            content['soup'] = soup
            
            # Try to get dynamic content with Selenium if available
            if self.driver:
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    dynamic_html = self.driver.page_source
                    dynamic_soup = BeautifulSoup(dynamic_html, 'html.parser')
                    
                    # Compare static vs dynamic content
                    if len(dynamic_soup.get_text()) > len(soup.get_text()) * 1.1:
                        content['html'] = dynamic_html
                        content['text'] = dynamic_soup.get_text(separator=' ', strip=True)
                        content['soup'] = dynamic_soup
                        content['dynamic_content'] = True
                    else:
                        content['dynamic_content'] = False
                        
                except Exception as e:
                    self.logger.warning(f"Selenium failed for {url}: {e}")
                    content['dynamic_content'] = False
            
        except Exception as e:
            self.logger.error(f"Failed to get content for {url}: {e}")
            raise
        
        return content
    
    def extract_journal_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract basic journal metadata"""
        metadata = {}
        
        # Journal title
        title_selectors = ['title', 'h1', '.journal-title', '#journal-title', '.title']
        metadata['title'] = self.get_text_by_selectors(soup, title_selectors)
        
        # ISSN extraction
        issn_pattern = r'\b\d{4}-\d{3}[\dX]\b'
        page_text = soup.get_text()
        issns = re.findall(issn_pattern, page_text)
        metadata['issns'] = list(set(issns))  # Remove duplicates
        
        # Publisher information
        publisher_selectors = ['.publisher', '#publisher', '.published-by']
        metadata['publisher'] = self.get_text_by_selectors(soup, publisher_selectors)
        
        # Impact factor claims
        if_pattern = r'impact\s+factor[\s:]*(\d+\.?\d*)'
        if_matches = re.findall(if_pattern, page_text.lower())
        metadata['claimed_impact_factor'] = if_matches[0] if if_matches else None
        
        # Subject areas
        subject_selectors = ['.subject', '.discipline', '.field', '.category']
        metadata['subjects'] = self.get_text_by_selectors(soup, subject_selectors)
        
        # Publication frequency
        freq_pattern = r'(monthly|quarterly|biannually|annually|weekly)'
        freq_matches = re.findall(freq_pattern, page_text.lower())
        metadata['frequency'] = freq_matches[0] if freq_matches else None
        
        return metadata
    
    async def analyze_editorial_board(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Analyze editorial board information"""
        editorial_info = {
            'board_size': 0,
            'members': [],
            'editor_in_chief': None,
            'quality_score': 0,
            'verification_notes': []
        }
        
        # Find editorial board section
        board_selectors = ['.editorial-board', '#editorial-board', '.editors', '#editors', 
                          '.board-members', '.editorial-team']
        
        board_section = None
        for selector in board_selectors:
            board_section = soup.select_one(selector)
            if board_section:
                break
        
        if not board_section:
            # Try to find by text content
            for div in soup.find_all(['div', 'section']):
                text = div.get_text().lower()
                if any(term in text for term in ['editorial board', 'editors', 'editorial team']):
                    board_section = div
                    break
        
        if board_section:
            # Extract member information
            member_elements = board_section.find_all(['div', 'li', 'tr'])
            
            for element in member_elements:
                text = element.get_text(strip=True)
                if len(text) > 10:  # Filter out empty or very short entries
                    member_info = self.parse_editor_info(text)
                    if member_info:
                        editorial_info['members'].append(member_info)
            
            editorial_info['board_size'] = len(editorial_info['members'])
            
            # Identify Editor-in-Chief
            for member in editorial_info['members']:
                if any(term in member.get('title', '').lower() 
                      for term in ['editor-in-chief', 'chief editor', 'editor in chief']):
                    editorial_info['editor_in_chief'] = member['name']
                    break
        
        # Calculate quality score
        editorial_info['quality_score'] = self.calculate_editorial_quality_score(editorial_info)
        
        return editorial_info
    
    def parse_editor_info(self, text: str) -> Optional[Dict]:
        """Parse individual editor information from text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return None
        
        info = {
            'raw_text': text,
            'name': lines[0] if lines else '',
            'title': '',
            'affiliation': '',
            'country': '',
            'email': ''
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            info['email'] = email_match.group()
        
        # Extract potential titles
        title_keywords = ['professor', 'dr.', 'ph.d', 'editor', 'associate', 'assistant']
        for line in lines[1:]:
            if any(keyword in line.lower() for keyword in title_keywords):
                info['title'] = line
                break
        
        # Extract affiliation (usually contains university, institute, etc.)
        affiliation_keywords = ['university', 'institute', 'college', 'hospital', 'center']
        for line in lines:
            if any(keyword in line.lower() for keyword in affiliation_keywords):
                info['affiliation'] = line
                break
        
        return info
    
    def calculate_editorial_quality_score(self, editorial_info: Dict) -> float:
        """Calculate quality score for editorial board (0-100)"""
        score = 0
        
        # Board size scoring
        size = editorial_info['board_size']
        if size >= 20:
            score += 30
        elif size >= 10:
            score += 20
        elif size >= 5:
            score += 10
        
        # Editor-in-Chief presence
        if editorial_info['editor_in_chief']:
            score += 20
        
        # Member information completeness
        complete_members = 0
        for member in editorial_info['members']:
            completeness = 0
            if member.get('name'):
                completeness += 1
            if member.get('affiliation'):
                completeness += 1
            if member.get('email'):
                completeness += 1
            if completeness >= 2:
                complete_members += 1
        
        if editorial_info['board_size'] > 0:
            completeness_ratio = complete_members / editorial_info['board_size']
            score += 30 * completeness_ratio
        
        # Diversity check (simple heuristic based on different affiliations)
        affiliations = set(member.get('affiliation', '').lower() 
                          for member in editorial_info['members'] 
                          if member.get('affiliation'))
        if len(affiliations) > editorial_info['board_size'] * 0.5:
            score += 20
        
        return min(score, 100)
    
    def extract_submission_info(self, soup: BeautifulSoup) -> Dict:
        """Extract submission guidelines and process information"""
        submission_info = {
            'has_guidelines': False,
            'review_process_described': False,
            'timeline_mentioned': False,
            'peer_review_mentioned': False,
            'submission_timeline': None,
            'review_timeline': None,
            'quality_score': 0
        }
        
        # Find submission-related content
        submission_selectors = ['.submission', '#submission', '.guidelines', '#guidelines',
                               '.authors', '#authors', '.instructions', '#instructions']
        
        submission_text = ''
        for selector in submission_selectors:
            element = soup.select_one(selector)
            if element:
                submission_text += element.get_text() + ' '
        
        # Check for submission guidelines
        guidelines_keywords = ['submission guidelines', 'author guidelines', 'instructions for authors']
        if any(keyword in submission_text.lower() for keyword in guidelines_keywords):
            submission_info['has_guidelines'] = True
            submission_info['quality_score'] += 25
        
        # Check for peer review mention
        peer_review_keywords = ['peer review', 'peer-review', 'reviewer', 'review process']
        if any(keyword in submission_text.lower() for keyword in peer_review_keywords):
            submission_info['peer_review_mentioned'] = True
            submission_info['quality_score'] += 25
        
        # Extract timelines
        timeline_patterns = [
            r'(\d+)\s*days?\s*(?:to|for)?\s*(?:review|decision)',
            r'(\d+)\s*weeks?\s*(?:to|for)?\s*(?:review|decision)',
            r'review\s*(?:process|time)[\s:]*(\d+)\s*(?:days?|weeks?)'
        ]
        
        for pattern in timeline_patterns:
            matches = re.findall(pattern, submission_text.lower())
            if matches:
                submission_info['timeline_mentioned'] = True
                submission_info['review_timeline'] = matches[0]
                submission_info['quality_score'] += 25
                break
        
        # Check for unrealistic claims
        suspicious_phrases = [
            'guaranteed acceptance', 'within 24 hours', 'immediate publication',
            'no peer review', 'pay after publication', 'fast track publication'
        ]
        
        for phrase in suspicious_phrases:
            if phrase in submission_text.lower():
                submission_info['quality_score'] = max(0, submission_info['quality_score'] - 30)
                break
        
        submission_info['quality_score'] = min(submission_info['quality_score'], 100)
        return submission_info
    
    def analyze_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Analyze contact information completeness and legitimacy"""
        contact_info = {
            'has_email': False,
            'has_phone': False,
            'has_address': False,
            'has_physical_address': False,
            'emails': [],
            'phones': [],
            'addresses': [],
            'quality_score': 0
        }
        
        page_text = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        contact_info['emails'] = list(set(emails))
        contact_info['has_email'] = len(emails) > 0
        
        # Extract phone numbers
        phone_patterns = [
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s?\d{3}-?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, page_text))
        
        contact_info['phones'] = list(set(phones))
        contact_info['has_phone'] = len(phones) > 0
        
        # Look for physical addresses
        address_keywords = ['address', 'location', 'office', 'street', 'building']
        contact_sections = soup.find_all(['div', 'section'], 
                                       class_=re.compile('contact|address', re.I))
        
        for section in contact_sections:
            text = section.get_text().lower()
            if any(keyword in text for keyword in address_keywords):
                contact_info['has_address'] = True
                contact_info['addresses'].append(section.get_text(strip=True))
        
        # Calculate quality score
        if contact_info['has_email']:
            contact_info['quality_score'] += 30
        if contact_info['has_phone']:
            contact_info['quality_score'] += 25
        if contact_info['has_address']:
            contact_info['quality_score'] += 25
        
        # Bonus for multiple contact methods
        if sum([contact_info['has_email'], contact_info['has_phone'], 
               contact_info['has_address']]) >= 2:
            contact_info['quality_score'] += 20
        
        return contact_info
    
    def extract_fees_info(self, soup: BeautifulSoup) -> Dict:
        """Extract publication fees information"""
        fees_info = {
            'has_fees': False,
            'fees_amount': None,
            'currency': None,
            'fees_description': '',
            'suspicious_payment': False,
            'quality_score': 0
        }
        
        page_text = soup.get_text().lower()
        
        # Fee-related keywords
        fee_keywords = ['publication fee', 'processing fee', 'apc', 'article processing charge',
                       'submission fee', 'handling fee', 'publication cost']
        
        fees_mentioned = any(keyword in page_text for keyword in fee_keywords)
        fees_info['has_fees'] = fees_mentioned
        
        if fees_mentioned:
            # Extract fee amounts
            fee_patterns = [
                r'(\$|€|£|USD|EUR|GBP)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(\$|€|£|USD|EUR|GBP)',
                r'(\d+)\s*(dollars?|euros?|pounds?)'
            ]
            
            for pattern in fee_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    fees_info['fees_amount'] = matches[0][1] if len(matches[0]) > 1 else matches[0][0]
                    fees_info['currency'] = matches[0][0] if len(matches[0]) > 1 else matches[0][1]
                    break
        
        # Check for suspicious payment methods
        suspicious_payment_keywords = ['bitcoin', 'paypal only', 'western union', 'moneygram',
                                     'cash only', 'personal account']
        
        if any(keyword in page_text for keyword in suspicious_payment_keywords):
            fees_info['suspicious_payment'] = True
            fees_info['quality_score'] -= 30
        
        # Reasonable fee assessment
        if fees_info['fees_amount']:
            try:
                amount = float(fees_info['fees_amount'].replace(',', ''))
                if amount > 3000:  # Very high fee
                    fees_info['quality_score'] -= 20
                elif amount > 2000:  # High fee
                    fees_info['quality_score'] -= 10
                elif 500 <= amount <= 1500:  # Reasonable range
                    fees_info['quality_score'] += 10
            except ValueError:
                pass
        
        return fees_info
    
    async def analyze_website_quality(self, url: str, content: Dict) -> Dict:
        """Analyze overall website quality and professionalism"""
        quality_metrics = {
            'design_score': 0,
            'technical_score': 0,
            'content_score': 0,
            'overall_score': 0,
            'issues': []
        }
        
        soup = content['soup']
        
        # Technical quality checks
        technical_score = 0
        
        # SSL certificate
        if url.startswith('https://'):
            technical_score += 20
        else:
            quality_metrics['issues'].append('No SSL certificate')
        
        # Responsive design check
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_tag:
            technical_score += 15
        else:
            quality_metrics['issues'].append('Not mobile responsive')
        
        # CSS and JavaScript presence
        css_links = soup.find_all('link', rel='stylesheet')
        js_scripts = soup.find_all('script')
        
        if len(css_links) > 0:
            technical_score += 10
        if len(js_scripts) > 0:
            technical_score += 10
        
        quality_metrics['technical_score'] = min(technical_score, 100)
        
        # Design quality assessment
        design_score = 0
        
        # Logo presence
        logo_selectors = ['img[alt*="logo" i]', '.logo', '#logo', 'img[src*="logo" i]']
        has_logo = any(soup.select(selector) for selector in logo_selectors)
        if has_logo:
            design_score += 20
        
        # Navigation menu
        nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile('nav|menu', re.I))
        if nav_elements:
            design_score += 20
        
        # Proper header structure
        headers = soup.find_all(['h1', 'h2', 'h3'])
        if len(headers) >= 3:
            design_score += 15
        
        quality_metrics['design_score'] = min(design_score, 100)
        
        # Content quality
        text_content = content['text']
        content_score = 0
        
        # Content length
        if len(text_content) > 1000:
            content_score += 20
        elif len(text_content) > 500:
            content_score += 10
        
        # Language quality (basic check)
        try:
            language = detect(text_content[:1000])  # Check first 1000 chars
            if language == 'en':
                content_score += 15
        except:
            pass
        
        # Readability
        if len(text_content) > 100:
            reading_ease = flesch_reading_ease(text_content[:5000])  # First 5000 chars
            if reading_ease >= 60:  # Fairly easy to read
                content_score += 15
            elif reading_ease >= 30:  # Difficult
                content_score += 5
        
        quality_metrics['content_score'] = min(content_score, 100)
        
        # Overall score
        quality_metrics['overall_score'] = (
            quality_metrics['technical_score'] * 0.3 +
            quality_metrics['design_score'] * 0.3 +
            quality_metrics['content_score'] * 0.4
        )
        
        return quality_metrics
    
    def analyze_content_quality(self, text: str) -> Dict:
        """Analyze text content quality using NLP techniques"""
        return self.text_analyzer.analyze_text_comprehensive(text)
    
    async def technical_analysis(self, url: str) -> Dict:
        """Perform technical analysis of the website"""
        analysis = {
            'domain_info': {},
            'ssl_info': {},
            'server_info': {},
            'security_score': 0
        }
        
        try:
            # Domain analysis
            domain = urlparse(url).netloc
            domain_info = self.domain_analyzer.analyze_domain(domain)
            analysis['domain_info'] = domain_info
            
            # Calculate security score based on domain analysis
            analysis['security_score'] = 100 - domain_info.get('risk_score', 50)
            
        except Exception as e:
            self.logger.error(f"Technical analysis failed for {url}: {e}")
        
        return analysis
    
    def get_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Helper method to extract text using CSS selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ""
    
    def __del__(self):
        """Cleanup selenium driver"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

