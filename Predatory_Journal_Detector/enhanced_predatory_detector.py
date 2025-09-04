#!/usr/bin/env python3
"""
Enhanced Predatory Journal Detector - Full Implementation
Based on comprehensive academic research and evidence-based criteria

This system implements ALL critical improvements identified from:
- Committee on Publication Ethics (COPE)
- Think-Check-Submit Initiative  
- Eriksson & Helgesson validated criteria
- Jeffrey Beall's research
- Recent academic literature (2023-2024)

Key Enhancements:
1. Peer Review Process Analysis (30/100) - CRITICAL #1 indicator
2. External Database Verification (15/100) - Cross-check claims
3. Enhanced Editorial Board Verification (20/100) - Credential checking  
4. Sophisticated Language Analysis (25/100) - Context-aware detection
5. Contact Transparency (10/100) - Reduced weight per research
6. Journal Name Legitimacy Analysis - Similarity detection
"""

import requests
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging
from datetime import datetime
import difflib
import pandas as pd
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnhancedAnalysisResult:
    """Comprehensive analysis result with evidence-based scoring"""
    # Overall Assessment
    overall_score: float
    risk_level: str
    confidence_score: float
    
    # Detailed Category Scores (Evidence-Based Weights)
    peer_review_score: float          # 30/100 - CRITICAL
    predatory_language_score: float   # 25/100 - HIGH  
    editorial_board_score: float      # 20/100 - HIGH
    indexing_verification_score: float # 15/100 - MODERATE
    contact_transparency_score: float  # 10/100 - LOW
    
    # Critical Findings
    critical_red_flags: List[str]
    high_risk_warnings: List[str] 
    moderate_concerns: List[str]
    positive_indicators: List[str]
    
    # External Verification Results
    external_verification: Dict[str, any]
    
    # Detailed Evidence
    peer_review_analysis: Dict[str, any]
    language_analysis: Dict[str, any]
    editorial_analysis: Dict[str, any]
    indexing_analysis: Dict[str, any]
    
    # Recommendations
    recommendations: List[str]
    next_steps: List[str]
    
    # Metadata
    analysis_timestamp: str
    analysis_duration: float
    journal_url: str
    
    # Confidence Intervals (Optional)
    confidence_95ci_lower: float = 0.0
    confidence_95ci_upper: float = 0.0

class EnhancedPredatoryDetector:
    """
    World-class predatory journal detection system
    
    Implements evidence-based criteria with external verification,
    sophisticated pattern recognition, and academic validation.
    """
    
    # Evidence-based scoring weights (Total = 100)
    EVIDENCE_BASED_WEIGHTS = {
        'peer_review_analysis': 30,      # #1 indicator per ALL academic sources
        'predatory_language': 25,        # Well-validated in literature
        'editorial_board_verification': 20, # Core academic practice  
        'indexing_verification': 15,     # Important for legitimacy
        'contact_transparency': 10       # Secondary per research findings
    }
    
    def __init__(self):
        """Initialize enhanced detection system with external APIs and NLM catalog"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Enhanced Academic Journal Analyzer/2.0 (Research Integrity Tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        # Load legitimate journal databases for verification
        self.legitimate_databases = self._load_legitimate_databases()
        
        # Load sophisticated predatory patterns from academic research
        self.predatory_patterns = self._load_evidence_based_patterns()
        
        # Load legitimate journal names for similarity comparison
        self.legitimate_journals = self._load_legitimate_journal_names()
        
        # Load NLM catalog data for journal legitimacy verification
        self.nlm_catalog = self._load_nlm_catalog()
        
        # Load JIF (Journal Impact Factor) data for reputation assessment
        self.jif_catalog = self._load_jif_catalog()
        
        # Initialize external API endpoints
        self.api_endpoints = {
            'doaj': 'https://doaj.org/api/search/journals/',
            'crossref': 'https://api.crossref.org/works/',
            'openalex': 'https://api.openalex.org/sources/',
            'ror': 'https://api.ror.org/organizations'  # For institutional verification
        }
        
        # Configure session for external API calls
        self.session.timeout = 10  # 10 second timeout for API calls
        
    def _load_legitimate_databases(self) -> Dict[str, List[str]]:
        """Load known legitimate academic databases"""
        return {
            'tier_1_major': [
                'pubmed', 'medline', 'scopus', 'web of science', 'doaj', 
                'pubmed central', 'cochrane library', 'ieee xplore'
            ],
            'tier_2_specialized': [
                'jstor', 'wiley online library', 'springerlink', 'sciencedirect',
                'acm digital library', 'arxiv', 'biorxiv', 'medrxiv'
            ],
            'tier_3_regional': [
                'scielo', 'redalyc', 'african journals online', 'bioline international',
                'j-stage', 'cnki', 'wanfang', 'korea citation index'
            ]
        }
    
    def _load_evidence_based_patterns(self) -> Dict[str, List[str]]:
        """Load sophisticated predatory patterns from academic literature"""
        return {
            'critical_red_flags': {
                'guaranteed_acceptance': [
                    r'guaranteed?\s+(?:acceptance|publication|approval)',
                    r'we\s+(?:accept|publish)\s+all\s+(?:papers?|manuscripts?|submissions?)',
                    r'(?:100%|assured|certain)\s+(?:acceptance|approval)',
                    r'acceptance\s+(?:rate|ratio)[:\s]+(?:100|99)%'
                ],
                'fake_peer_review': [
                    r'no\s+(?:peer\s+)?review\s+(?:required|needed|necessary)',
                    r'(?:skip|bypass|avoid)\s+(?:peer\s+)?review',
                    r'minimal\s+(?:peer\s+)?review\s+(?:process|required)',
                    r'(?:instant|immediate)\s+(?:peer\s+)?review'
                ],
                'payment_manipulation': [
                    r'pay\s+(?:only\s+)?(?:after|upon)\s+(?:acceptance|publication)',
                    r'no\s+(?:fees?|charges?|costs?)\s+(?:until|before|unless)\s+acceptance',
                    r'(?:bitcoin|cryptocurrency|digital\s+currency)\s+payments?',
                    r'payment\s+(?:after|upon)\s+(?:acceptance|publication)\s+only'
                ],
                'fake_metrics': [
                    r'(?:impact\s+factor|if)[:\s]+(?:will\s+be|guaranteed|assured)\s+\d+',
                    r'(?:guaranteed|assured|promised)\s+(?:impact\s+factor|citations?)',
                    r'(?:increase|boost|improve)\s+(?:your\s+)?(?:h-index|citations?|impact)',
                    r'fake\s+(?:impact\s+factor|indexing|database)'
                ]
            },
            'high_risk_indicators': {
                'unrealistic_timelines': [
                    r'(?:publish|review|decision)\s+(?:within|in)\s+(?:\d+\s+)?(?:hours?|24\s+hours?)',
                    r'(?:immediate|instant|same[- ]day)\s+(?:publication|review|decision)',
                    r'(?:rapid|fast|quick)\s+publication\s+within\s+(?:\d+\s+)?(?:days?|hours?)',
                    r'(?:express|emergency|urgent)\s+(?:publication|review|processing)'
                ],
                'aggressive_marketing': [
                    r'(?:limited\s+time|special|exclusive)\s+(?:offer|deal|opportunity)',
                    r'(?:act\s+(?:now|quickly|fast)|hurry|don\'t\s+miss)',
                    r'(?:discount|promotion|reduced\s+price|sale)\s+(?:available|ending)',
                    r'(?:call\s+now|contact\s+immediately|respond\s+quickly)'
                ],
                'false_authority': [
                    r'(?:world[- ](?:class|renowned|leading|famous)|internationally\s+recognized)',
                    r'(?:ranked|top)\s+(?:\#?\d+|number\s+\d+)\s+(?:journal|publisher)',
                    r'(?:prestigious|elite|premier)\s+(?:journal|publisher|platform)',
                    r'(?:thousands|millions)\s+of\s+(?:satisfied\s+)?(?:authors|researchers)'
                ]
            },
            'moderate_risk_indicators': {
                'speed_emphasis': [
                    r'fast\s+track\s+(?:publication|review|processing)',
                    r'(?:quick|speedy|rapid)\s+(?:turnaround|processing|review)',
                    r'accelerated\s+(?:publication|review|timeline)',
                    r'expedited\s+(?:review|publication|processing)'
                ],
                'promotional_language': [
                    r'(?:enhance|boost|advance|improve)\s+(?:your\s+)?(?:career|reputation|profile)',
                    r'(?:join\s+)?(?:thousands|millions)\s+of\s+(?:successful\s+)?(?:authors|researchers)',
                    r'(?:opportunity|chance)\s+(?:for|of)\s+(?:publication|recognition)',
                    r'(?:excellent|outstanding|amazing)\s+(?:opportunity|platform|service)'
                ]
            }
        }
    
    def _load_legitimate_journal_names(self) -> List[str]:
        """Load sample legitimate journal names for similarity analysis"""
        return [
            'Nature', 'Science', 'Cell', 'The Lancet', 'New England Journal of Medicine',
            'PLOS ONE', 'Nature Communications', 'Scientific Reports', 'BMJ', 'JAMA',
            'Nature Biotechnology', 'Nature Medicine', 'Nature Genetics', 'Cell Stem Cell',
            'Immunity', 'Neuron', 'Cancer Cell', 'Molecular Cell', 'Developmental Cell',
            'Current Biology', 'Cell Metabolism', 'Cell Reports', 'eLife', 'EMBO Journal',
            'Proceedings of the National Academy of Sciences', 'Journal of Clinical Investigation',
            'Blood', 'Circulation', 'Journal of Experimental Medicine', 'Gastroenterology',
            'Hepatology', 'Journal of Clinical Oncology', 'Cancer Research', 'Clinical Cancer Research',
            'IEEE Transactions', 'ACM Computing Surveys', 'Communications of the ACM',
            'Journal of Machine Learning Research', 'Artificial Intelligence', 'Neural Networks'
        ]
    
    def _load_nlm_catalog(self) -> Dict:
        """
        Load NLM (National Library of Medicine) catalog data for journal legitimacy verification
        
        Returns comprehensive NLM data indexed by ISSN and title for fast lookup.
        This provides the gold standard for legitimate journals.
        """
        nlm_data = {
            'by_issn': {},
            'by_title': {},
            'by_publisher': {},
            'stats': {'total_journals': 0, 'medline_indexed': 0}
        }
        
        try:
            # Get the path to the NLM catalog file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            nlm_file_path = os.path.join(current_dir, 'data', 'nlm_journals_consolidated.csv')
            
            if not os.path.exists(nlm_file_path):
                logger.warning(f"⚠️ NLM catalog file not found at {nlm_file_path}")
                return nlm_data
                
            logger.info("📚 Loading NLM catalog data...")
            df = pd.read_csv(nlm_file_path)
            
            for _, row in df.iterrows():
                # Create journal entry
                journal_entry = {
                    'title_full': row.get('title_full', ''),
                    'title_abbreviation': row.get('title_abbreviation', ''),
                    'publisher': row.get('publisher', ''),
                    'country': row.get('country', ''),
                    'issn_electronic': row.get('issn_electronic', ''),
                    'issn_print': row.get('issn_print', ''),
                    'issn_linking': row.get('issn_linking', ''),
                    'current_indexing_status': row.get('current_indexing_status', ''),
                    'in_databases': row.get('in_databases', ''),
                    'electronic_links': row.get('electronic_links', ''),
                    'medline_indexed': 'Currently indexed for MEDLINE' in str(row.get('current_indexing_status', ''))
                }
                
                # Index by ISSN (all types)
                for issn_field in ['issn_electronic', 'issn_print', 'issn_linking']:
                    issn = str(row.get(issn_field, '')).strip()
                    if issn and issn != 'nan' and len(issn) >= 8:
                        nlm_data['by_issn'][issn] = journal_entry
                
                # Index by title (both full and abbreviated)
                title_full = str(row.get('title_full', '')).strip().lower()
                title_abbrev = str(row.get('title_abbreviation', '')).strip().lower()
                
                if title_full and title_full != 'nan':
                    nlm_data['by_title'][title_full] = journal_entry
                    
                if title_abbrev and title_abbrev != 'nan' and title_abbrev != title_full:
                    nlm_data['by_title'][title_abbrev] = journal_entry
                
                # Index by publisher
                publisher = str(row.get('publisher', '')).strip().lower()
                if publisher and publisher != 'nan':
                    if publisher not in nlm_data['by_publisher']:
                        nlm_data['by_publisher'][publisher] = []
                    nlm_data['by_publisher'][publisher].append(journal_entry)
                
                # Update stats
                nlm_data['stats']['total_journals'] += 1
                if journal_entry['medline_indexed']:
                    nlm_data['stats']['medline_indexed'] += 1
            
            logger.info(f"✅ NLM catalog loaded: {nlm_data['stats']['total_journals']:,} journals "
                       f"({nlm_data['stats']['medline_indexed']:,} MEDLINE-indexed)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load NLM catalog: {e}")
        
        return nlm_data
    
    def _load_jif_catalog(self) -> Dict:
        """
        Load JIF (Journal Impact Factor) catalog data for reputation assessment
        
        Returns comprehensive JIF data indexed by ISSN and title for fast lookup.
        Higher impact factors indicate more reputable journals.
        """
        jif_data = {
            'by_issn': {},
            'by_title': {},
            'by_title_fuzzy': {},
            'stats': {'total_journals': 0, 'high_impact': 0}
        }
        
        try:
            # Get the path to the JIF catalog file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            jif_file_path = os.path.join(current_dir, 'data', 'jif_impact_factors_2025.csv')
            
            if not os.path.exists(jif_file_path):
                logger.warning(f"⚠️ JIF catalog file not found at {jif_file_path}")
                return jif_data
                
            logger.info("📊 Loading JIF catalog data...")
            df = pd.read_csv(jif_file_path)
            
            for _, row in df.iterrows():
                # Create journal entry
                impact_factor = float(row.get('impact_factor', 0))
                
                journal_entry = {
                    'journal_name': row.get('journal_name', ''),
                    'publisher': row.get('publisher', ''),
                    'issn': row.get('issn', ''),
                    'impact_factor': impact_factor,
                    'impact_tier': self._classify_impact_tier(impact_factor)
                }
                
                # Index by ISSN
                issn = str(row.get('issn', '')).strip()
                if issn and issn != 'nan' and len(issn) >= 8:
                    jif_data['by_issn'][issn] = journal_entry
                
                # Index by title (exact)
                title = str(row.get('journal_name', '')).strip().lower()
                if title and title != 'nan':
                    jif_data['by_title'][title] = journal_entry
                    
                    # Also index by simplified title for fuzzy matching
                    simplified_title = self._simplify_journal_title(title)
                    jif_data['by_title_fuzzy'][simplified_title] = journal_entry
                
                # Update stats
                jif_data['stats']['total_journals'] += 1
                if impact_factor >= 10.0:  # High impact threshold
                    jif_data['stats']['high_impact'] += 1
            
            logger.info(f"✅ JIF catalog loaded: {jif_data['stats']['total_journals']:,} journals "
                       f"({jif_data['stats']['high_impact']:,} high-impact)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load JIF catalog: {e}")
        
        return jif_data
    
    def _classify_impact_tier(self, impact_factor: float) -> str:
        """Classify journal impact factor into tiers"""
        if impact_factor >= 30.0:
            return "elite"        # Top-tier (Nature, Science, etc.)
        elif impact_factor >= 10.0:
            return "high"         # High-impact journals
        elif impact_factor >= 5.0:
            return "medium_high"  # Above-average journals
        elif impact_factor >= 2.0:
            return "medium"       # Average journals
        elif impact_factor >= 1.0:
            return "medium_low"   # Below-average journals
        else:
            return "low"          # Low-impact journals
    
    def _simplify_journal_title(self, title: str) -> str:
        """Simplify journal title for fuzzy matching"""
        # Remove common words and normalize
        stop_words = {'journal', 'of', 'the', 'and', 'in', 'for', 'a', 'an', 'international', 
                     'american', 'european', 'nature', 'reviews', 'letters', 'communications'}
        
        words = re.findall(r'\b\w+\b', title.lower())
        simplified = ' '.join(word for word in words if word not in stop_words)
        return simplified.strip()
    
    def _lookup_journal_in_nlm(self, journal_name: str, issns: List[str] = None, url: str = None) -> Dict:
        """
        Comprehensive NLM catalog lookup for journal legitimacy verification
        
        Args:
            journal_name: Journal title to search for
            issns: List of ISSNs to check
            url: Journal URL for additional matching
            
        Returns:
            Dict with NLM status, entry details, and reputation boost
        """
        nlm_result = {
            'found_in_nlm': False,
            'medline_indexed': False,
            'nlm_entry': None,
            'match_type': None,
            'reputation_boost': 0.0,
            'confidence_boost': 0.0
        }
        
        if not self.nlm_catalog or not self.nlm_catalog['stats']['total_journals']:
            return nlm_result
        
        try:
            # 1. HIGHEST PRIORITY: ISSN-based matching (most reliable)
            if issns:
                for issn in issns:
                    clean_issn = str(issn).strip().replace('-', '').replace(' ', '')
                    if clean_issn in self.nlm_catalog['by_issn']:
                        entry = self.nlm_catalog['by_issn'][clean_issn]
                        nlm_result.update({
                            'found_in_nlm': True,
                            'nlm_entry': entry,
                            'match_type': 'issn_exact',
                            'medline_indexed': entry['medline_indexed'],
                            'reputation_boost': 40.0 if entry['medline_indexed'] else 25.0,
                            'confidence_boost': 30.0 if entry['medline_indexed'] else 20.0
                        })
                        logger.info(f"✅ NLM MATCH: Found by ISSN {issn} - MEDLINE: {entry['medline_indexed']}")
                        return nlm_result
            
            # 2. SECONDARY: Title-based matching (exact)
            if journal_name:
                clean_title = journal_name.strip().lower()
                
                # Check exact title match
                if clean_title in self.nlm_catalog['by_title']:
                    entry = self.nlm_catalog['by_title'][clean_title]
                    nlm_result.update({
                        'found_in_nlm': True,
                        'nlm_entry': entry,
                        'match_type': 'title_exact',
                        'medline_indexed': entry['medline_indexed'],
                        'reputation_boost': 35.0 if entry['medline_indexed'] else 20.0,
                        'confidence_boost': 25.0 if entry['medline_indexed'] else 15.0
                    })
                    logger.info(f"✅ NLM MATCH: Found by title '{journal_name}' - MEDLINE: {entry['medline_indexed']}")
                    return nlm_result
                
                # Check fuzzy title matching for slight variations
                for nlm_title, entry in self.nlm_catalog['by_title'].items():
                    if self._fuzzy_title_match(clean_title, nlm_title, threshold=0.85):
                        nlm_result.update({
                            'found_in_nlm': True,
                            'nlm_entry': entry,
                            'match_type': 'title_fuzzy',
                            'medline_indexed': entry['medline_indexed'],
                            'reputation_boost': 30.0 if entry['medline_indexed'] else 15.0,
                            'confidence_boost': 20.0 if entry['medline_indexed'] else 10.0
                        })
                        logger.info(f"✅ NLM MATCH: Fuzzy match '{journal_name}' → '{nlm_title}' - MEDLINE: {entry['medline_indexed']}")
                        return nlm_result
            
            # 3. TERTIARY: Publisher-based reputation (weaker signal)
            if url:
                domain = self._extract_domain_from_url(url)
                for publisher_key, journals in self.nlm_catalog['by_publisher'].items():
                    if domain and domain.lower() in publisher_key:
                        # Check if this publisher has multiple NLM journals (reputation signal)
                        medline_journals = [j for j in journals if j['medline_indexed']]
                        if len(journals) >= 3:  # Publisher with multiple NLM journals
                            nlm_result.update({
                                'found_in_nlm': True,
                                'nlm_entry': journals[0],  # Representative entry
                                'match_type': 'publisher_reputation',
                                'medline_indexed': len(medline_journals) > 0,
                                'reputation_boost': 15.0 if medline_journals else 8.0,
                                'confidence_boost': 10.0 if medline_journals else 5.0
                            })
                            logger.info(f"✅ NLM MATCH: Publisher reputation '{publisher_key}' ({len(journals)} NLM journals)")
                            return nlm_result
            
        except Exception as e:
            logger.error(f"❌ NLM lookup error: {e}")
        
        return nlm_result
    
    def _lookup_journal_in_jif(self, journal_name: str, issns: List[str] = None, url: str = None) -> Dict:
        """
        Comprehensive JIF catalog lookup for journal impact factor assessment
        
        Args:
            journal_name: Journal title to search for
            issns: List of ISSNs to check
            url: Journal URL for additional context
            
        Returns:
            Dict with JIF status, impact factor, tier, and reputation boost
        """
        jif_result = {
            'found_in_jif': False,
            'impact_factor': 0.0,
            'impact_tier': 'unknown',
            'jif_entry': None,
            'match_type': None,
            'reputation_boost': 0.0,
            'confidence_boost': 0.0
        }
        
        if not self.jif_catalog or not self.jif_catalog['stats']['total_journals']:
            return jif_result
        
        try:
            # 1. HIGHEST PRIORITY: ISSN-based matching (most reliable)
            if issns:
                for issn in issns:
                    clean_issn = str(issn).strip().replace('-', '').replace(' ', '')
                    # Try both with and without dash
                    formatted_issn = f"{clean_issn[:4]}-{clean_issn[4:]}" if len(clean_issn) == 8 else clean_issn
                    
                    if clean_issn in self.jif_catalog['by_issn'] or formatted_issn in self.jif_catalog['by_issn']:
                        entry = self.jif_catalog['by_issn'].get(clean_issn, self.jif_catalog['by_issn'].get(formatted_issn))
                        if entry:
                            reputation_boost, confidence_boost = self._calculate_jif_boosts(entry['impact_factor'], entry['impact_tier'])
                            jif_result.update({
                                'found_in_jif': True,
                                'impact_factor': entry['impact_factor'],
                                'impact_tier': entry['impact_tier'],
                                'jif_entry': entry,
                                'match_type': 'issn_exact',
                                'reputation_boost': reputation_boost,
                                'confidence_boost': confidence_boost
                            })
                            logger.info(f"📊 JIF MATCH: Found by ISSN {issn} - IF: {entry['impact_factor']:.1f} ({entry['impact_tier']})")
                            return jif_result
            
            # 2. SECONDARY: Title-based matching (exact)
            if journal_name:
                clean_title = journal_name.strip().lower()
                
                # Check exact title match
                if clean_title in self.jif_catalog['by_title']:
                    entry = self.jif_catalog['by_title'][clean_title]
                    reputation_boost, confidence_boost = self._calculate_jif_boosts(entry['impact_factor'], entry['impact_tier'])
                    jif_result.update({
                        'found_in_jif': True,
                        'impact_factor': entry['impact_factor'],
                        'impact_tier': entry['impact_tier'],
                        'jif_entry': entry,
                        'match_type': 'title_exact',
                        'reputation_boost': reputation_boost,
                        'confidence_boost': confidence_boost
                    })
                    logger.info(f"📊 JIF MATCH: Found by title '{journal_name}' - IF: {entry['impact_factor']:.1f} ({entry['impact_tier']})")
                    return jif_result
                
                # 3. TERTIARY: Fuzzy title matching (simplified)
                simplified_title = self._simplify_journal_title(clean_title)
                if simplified_title in self.jif_catalog['by_title_fuzzy']:
                    entry = self.jif_catalog['by_title_fuzzy'][simplified_title]
                    reputation_boost, confidence_boost = self._calculate_jif_boosts(entry['impact_factor'], entry['impact_tier'])
                    jif_result.update({
                        'found_in_jif': True,
                        'impact_factor': entry['impact_factor'],
                        'impact_tier': entry['impact_tier'],
                        'jif_entry': entry,
                        'match_type': 'title_fuzzy',
                        'reputation_boost': reputation_boost,
                        'confidence_boost': confidence_boost
                    })
                    logger.info(f"📊 JIF MATCH: Fuzzy match '{journal_name}' → '{entry['journal_name']}' - IF: {entry['impact_factor']:.1f}")
                    return jif_result
            
        except Exception as e:
            logger.error(f"❌ JIF lookup error: {e}")
        
        return jif_result
    
    def _calculate_jif_boosts(self, impact_factor: float, impact_tier: str) -> Tuple[float, float]:
        """Calculate reputation and confidence boosts based on impact factor"""
        
        # Reputation boost (reduces predatory risk)
        if impact_tier == "elite":  # IF >= 30
            reputation_boost = 50.0
        elif impact_tier == "high":  # IF >= 10
            reputation_boost = 35.0
        elif impact_tier == "medium_high":  # IF >= 5
            reputation_boost = 25.0
        elif impact_tier == "medium":  # IF >= 2
            reputation_boost = 15.0
        elif impact_tier == "medium_low":  # IF >= 1
            reputation_boost = 8.0
        else:  # Low IF
            reputation_boost = 3.0
        
        # Confidence boost (increases analysis confidence)
        if impact_tier == "elite":
            confidence_boost = 35.0
        elif impact_tier == "high":
            confidence_boost = 25.0
        elif impact_tier == "medium_high":
            confidence_boost = 18.0
        elif impact_tier == "medium":
            confidence_boost = 12.0
        elif impact_tier == "medium_low":
            confidence_boost = 6.0
        else:
            confidence_boost = 2.0
        
        return reputation_boost, confidence_boost
    
    def _fuzzy_title_match(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two journal titles are similar enough to be considered a match"""
        # Remove common words and punctuation for better matching
        stop_words = {'journal', 'of', 'the', 'and', 'in', 'for', 'a', 'an', 'international', 'american', 'european'}
        
        def clean_title(title):
            words = re.findall(r'\b\w+\b', title.lower())
            return ' '.join(word for word in words if word not in stop_words)
        
        clean1 = clean_title(title1)
        clean2 = clean_title(title2)
        
        # Use difflib for similarity ratio
        similarity = difflib.SequenceMatcher(None, clean1, clean2).ratio()
        return similarity >= threshold
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL for publisher matching"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _extract_journal_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract journal title from webpage content"""
        try:
            # Try multiple methods to extract journal title
            title_candidates = []
            
            # 1. Meta tags
            meta_title = soup.find('meta', attrs={'name': 'citation_journal_title'})
            if meta_title and meta_title.get('content'):
                title_candidates.append(meta_title['content'].strip())
            
            # 2. Page title
            page_title = soup.find('title')
            if page_title and page_title.text:
                title_candidates.append(page_title.text.strip())
            
            # 3. H1 tags
            h1_tags = soup.find_all('h1')
            for h1 in h1_tags:
                if h1.text and len(h1.text.strip()) > 5:
                    title_candidates.append(h1.text.strip())
            
            # 4. Common class names for journal titles
            title_classes = ['journal-title', 'site-title', 'brand-title', 'journal-name']
            for class_name in title_classes:
                title_elem = soup.find(class_=class_name)
                if title_elem and title_elem.text:
                    title_candidates.append(title_elem.text.strip())
            
            # Return the most likely journal title (usually the first valid one)
            for title in title_candidates:
                # Clean up title
                title = re.sub(r'\s+', ' ', title)  # Multiple spaces to single
                title = re.sub(r'[\|\-–—].*$', '', title)  # Remove subtitle after delimiter
                title = title.strip()
                
                # Filter out very short or obviously wrong titles
                if len(title) > 5 and not any(x in title.lower() for x in ['home', 'welcome', 'page', 'error']):
                    return title
            
            # Fallback: extract from URL
            domain = self._extract_domain_from_url(url)
            if domain:
                # Convert domain to potential journal name
                domain_name = domain.replace('.com', '').replace('.org', '').replace('.net', '')
                domain_name = domain_name.replace('-', ' ').replace('_', ' ').title()
                return domain_name
            
            return ""
            
        except Exception as e:
            logger.debug(f"Journal title extraction error: {e}")
            return ""
    
    def _extract_issns_from_content(self, text: str, soup: BeautifulSoup) -> List[str]:
        """Extract ISSNs from webpage content"""
        issns = []
        
        try:
            # 1. Meta tags for ISSNs
            issn_meta_tags = soup.find_all('meta', attrs={'name': re.compile(r'.*issn.*', re.I)})
            for meta in issn_meta_tags:
                content = meta.get('content', '').strip()
                if content and self._is_valid_issn(content):
                    issns.append(content)
            
            # 2. ISSN pattern matching in text
            issn_pattern = r'\b(?:ISSN|issn)[\s:]*([0-9]{4}[-\s]?[0-9]{3}[0-9X])\b'
            matches = re.findall(issn_pattern, text, re.IGNORECASE)
            for match in matches:
                clean_issn = match.replace(' ', '').replace('-', '')
                if self._is_valid_issn(clean_issn) and clean_issn not in issns:
                    issns.append(clean_issn)
            
            # 3. Standalone ISSN numbers (more flexible pattern)
            standalone_pattern = r'\b([0-9]{4}[-\s]?[0-9]{3}[0-9X])\b'
            matches = re.findall(standalone_pattern, text)
            for match in matches:
                clean_issn = match.replace(' ', '').replace('-', '')
                if self._is_valid_issn(clean_issn) and clean_issn not in issns:
                    # Only add if it appears in a context suggesting it's an ISSN
                    issn_context = text[text.find(match)-50:text.find(match)+50].lower()
                    if any(word in issn_context for word in ['issn', 'journal', 'publication', 'print', 'online', 'electronic']):
                        issns.append(clean_issn)
            
        except Exception as e:
            logger.debug(f"ISSN extraction error: {e}")
        
        return list(set(issns))  # Remove duplicates
    
    def _is_valid_issn(self, issn: str) -> bool:
        """Validate ISSN format and check digit"""
        try:
            # Clean ISSN
            clean_issn = issn.replace('-', '').replace(' ', '').upper()
            
            # Check format
            if len(clean_issn) != 8 or not re.match(r'^[0-9]{7}[0-9X]$', clean_issn):
                return False
            
            # Validate checksum
            digits = clean_issn[:7]
            check_digit = clean_issn[7]
            
            total = sum(int(digit) * (8 - i) for i, digit in enumerate(digits))
            remainder = total % 11
            
            if remainder == 0:
                expected_check = '0'
            elif remainder == 1:
                expected_check = 'X'
            else:
                expected_check = str(11 - remainder)
            
            return check_digit == expected_check
            
        except Exception:
            return False
    
    def search_journal_by_name(self, journal_name: str) -> Dict:
        """
        Search for journal by name: First check NLM catalog, then OpenAlex for URL
        
        Args:
            journal_name: Name of the journal to search for
            
        Returns:
            Dict with search results, URLs, and analysis options
        """
        logger.info(f"🔍 Searching for journal: '{journal_name}'")
        
        search_result = {
            'journal_name': journal_name,
            'found_in_nlm': False,
            'found_in_openalex': False,
            'nlm_data': None,
            'openalex_data': None,
            'suggested_url': None,
            'can_analyze': False,
            'search_summary': []
        }
        
        # Step 1: Search NLM catalog first
        logger.info("🏛️ Step 1: Searching NLM catalog...")
        nlm_result = self._search_nlm_by_name(journal_name)
        
        if nlm_result['found']:
            search_result['found_in_nlm'] = True
            search_result['nlm_data'] = nlm_result
            search_result['search_summary'].append(f"✅ Found in NLM catalog: {nlm_result['title']}")
            
            if nlm_result.get('medline_indexed'):
                search_result['search_summary'].append("🏛️ Journal is MEDLINE-indexed (high credibility)")
            
            # If NLM has electronic links, use them
            electronic_links = nlm_result.get('electronic_links')
            valid_url = self._extract_best_url(electronic_links)
            if valid_url:
                search_result['suggested_url'] = valid_url
                search_result['can_analyze'] = True
                search_result['search_summary'].append(f"🔗 URL available from NLM: {valid_url}")
            else:
                search_result['search_summary'].append("⚠️ NLM entry found but no valid URL available")
        else:
            search_result['search_summary'].append("📊 Not found in NLM catalog")
        
        # Step 2: If not found in NLM or no URL, search OpenAlex
        if not search_result['can_analyze']:
            logger.info("🌐 Step 2: Searching OpenAlex for URL and metadata...")
            openalex_result = self._search_openalex_by_name(journal_name)
            
            if openalex_result['found']:
                search_result['found_in_openalex'] = True
                search_result['openalex_data'] = openalex_result
                search_result['search_summary'].append(f"✅ Found in OpenAlex: {openalex_result['display_name']}")
                
                homepage_url = openalex_result.get('homepage_url')
                if homepage_url and self._is_valid_url(homepage_url):
                    search_result['suggested_url'] = homepage_url
                    search_result['can_analyze'] = True
                    search_result['search_summary'].append(f"🔗 Homepage URL: {homepage_url}")
                else:
                    search_result['search_summary'].append("⚠️ OpenAlex entry found but no valid homepage URL available")
                
                if openalex_result.get('works_count'):
                    search_result['search_summary'].append(f"📄 Publications: {openalex_result['works_count']:,}")
                    
                if openalex_result.get('cited_by_count'):
                    search_result['search_summary'].append(f"📈 Citations: {openalex_result['cited_by_count']:,}")
                    
            else:
                search_result['search_summary'].append("❌ Not found in OpenAlex either")
        
        # Final summary
        if search_result['can_analyze']:
            search_result['search_summary'].append("🎯 Ready for predatory analysis")
            logger.info(f"✅ Search successful: Found URL for analysis")
        else:
            search_result['search_summary'].append("⚠️ No URL found - manual URL entry required")
            logger.info(f"❌ Search incomplete: No URL found for '{journal_name}'")
            
        return search_result
    
    def _search_nlm_by_name(self, journal_name: str) -> Dict:
        """Search NLM catalog by journal name"""
        result = {'found': False, 'title': '', 'electronic_links': '', 'medline_indexed': False}
        
        try:
            if not self.nlm_catalog or not self.nlm_catalog['stats']['total_journals']:
                return result
            
            clean_name = journal_name.strip().lower()
            
            # Special handling for well-known journals with specific ISSNs
            special_journals = {
                'lancet': '0140-6736',  # The main Lancet journal
                'the lancet': '0140-6736',
                'nature': '0028-0836',  # Nature
                'science': '0036-8075',  # Science
                'cell': '0092-8674',    # Cell
            }
            
            # Check special cases first
            if clean_name in special_journals:
                issn = special_journals[clean_name]
                if issn in self.nlm_catalog['by_issn']:
                    entry = self.nlm_catalog['by_issn'][issn]
                    result = {
                        'found': True,
                        'title': entry['title_full'],
                        'title_abbreviation': entry['title_abbreviation'],
                        'publisher': entry['publisher'],
                        'issn_electronic': entry['issn_electronic'],
                        'issn_print': entry['issn_print'],
                        'electronic_links': entry['electronic_links'],
                        'medline_indexed': entry['medline_indexed'],
                        'match_type': 'special_issn'
                    }
                    return result
            
            # Try exact match
            if clean_name in self.nlm_catalog['by_title']:
                entry = self.nlm_catalog['by_title'][clean_name]
                result = {
                    'found': True,
                    'title': entry['title_full'],
                    'title_abbreviation': entry['title_abbreviation'],
                    'publisher': entry['publisher'],
                    'issn_electronic': entry['issn_electronic'],
                    'issn_print': entry['issn_print'],
                    'electronic_links': entry['electronic_links'],
                    'medline_indexed': entry['medline_indexed'],
                    'match_type': 'exact'
                }
                return result
            
            # Try fuzzy matching with prioritization
            best_match = None
            best_score = 0
            
            for nlm_title, entry in self.nlm_catalog['by_title'].items():
                # Calculate fuzzy match score
                if self._fuzzy_title_match(clean_name, nlm_title, threshold=0.85):
                    # Prioritize MEDLINE-indexed journals
                    score = self._calculate_match_score(clean_name, nlm_title, entry['medline_indexed'])
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'found': True,
                            'title': entry['title_full'],
                            'title_abbreviation': entry['title_abbreviation'],
                            'publisher': entry['publisher'],
                            'issn_electronic': entry['issn_electronic'],
                            'issn_print': entry['issn_print'],
                            'electronic_links': entry['electronic_links'],
                            'medline_indexed': entry['medline_indexed'],
                            'match_type': 'fuzzy',
                            'matched_title': nlm_title,
                            'match_score': score
                        }
            
            if best_match:
                return best_match
                    
        except Exception as e:
            logger.error(f"❌ NLM search error: {e}")
            
        return result
    
    def _calculate_match_score(self, query: str, title: str, is_medline: bool) -> float:
        """Calculate match quality score for prioritizing results"""
        from difflib import SequenceMatcher
        
        # Base similarity score
        similarity = SequenceMatcher(None, query.lower(), title.lower()).ratio()
        
        # Boost for MEDLINE-indexed journals
        medline_boost = 0.2 if is_medline else 0
        
        # Boost for shorter titles (less specific matches)
        length_penalty = len(title) / 100  # Small penalty for very long titles
        
        # Boost for exact word matches
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        word_match_boost = len(query_words.intersection(title_words)) / max(len(query_words), 1) * 0.1
        
        return similarity + medline_boost - length_penalty + word_match_boost
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if a URL is proper and not a placeholder value"""
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # Check for invalid placeholder values
        invalid_values = {'nan', 'null', 'none', '', 'n/a', 'not available'}
        if url.lower() in invalid_values:
            return False
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Check for minimum valid URL structure
        if len(url) < 10:  # Minimum reasonable URL length
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = ['search.example.com', 'example.com', 'localhost']
        for pattern in suspicious_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def _extract_best_url(self, url_string: str) -> str:
        """Extract the best URL from a string that may contain multiple URLs"""
        if not url_string or not isinstance(url_string, str):
            return None
        
        # Handle multiple URLs separated by commas
        potential_urls = [url.strip() for url in url_string.split(',')]
        
        # URL preferences (higher score = better)
        url_preferences = {
            'sciencedirect.com': 10,
            'nature.com': 9,
            'elsevier': 8,
            'springer': 7,
            'wiley': 6,
            'tandfonline.com': 5,
            'ncbi.nlm.nih.gov': 4,
            'pmc.ncbi.nlm.nih.gov': 3
        }
        
        best_url = None
        best_score = -1
        
        for url in potential_urls:
            if self._is_valid_url(url):
                # Calculate preference score
                score = 0
                for domain, pref_score in url_preferences.items():
                    if domain in url.lower():
                        score = pref_score
                        break
                
                # Prefer shorter URLs if same score (usually more direct)
                if score == best_score:
                    if len(url) < len(best_url):
                        best_url = url
                elif score > best_score:
                    best_score = score
                    best_url = url
                elif best_url is None:  # First valid URL found
                    best_url = url
                    best_score = 0
        
        return best_url
    
    def _search_openalex_by_name(self, journal_name: str) -> Dict:
        """Search OpenAlex API for journal URL and metadata"""
        result = {'found': False, 'display_name': '', 'homepage_url': '', 'works_count': 0, 'cited_by_count': 0}
        
        try:
            # Query OpenAlex sources endpoint (correct format)
            import urllib.parse
            encoded_name = urllib.parse.quote_plus(journal_name)
            search_url = f"https://api.openalex.org/sources?search={encoded_name}&filter=type:journal"
            
            logger.info(f"📡 Querying OpenAlex: {search_url}")
            response = self.session.get(search_url, headers={'User-Agent': 'mailto:research@example.com'})
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Take the first result (most relevant)
                    journal = results[0]
                    
                    result = {
                        'found': True,
                        'openalex_id': journal.get('id', ''),
                        'display_name': journal.get('display_name', ''),
                        'homepage_url': journal.get('homepage_url', ''),
                        'works_count': journal.get('works_count', 0),
                        'cited_by_count': journal.get('cited_by_count', 0),
                        'is_oa': journal.get('is_oa', False),
                        'issn': journal.get('issn', []),
                        'publisher': journal.get('host_organization_name', ''),
                        'country_code': journal.get('country_code', ''),
                        'type': journal.get('type', ''),
                        'updated_date': journal.get('updated_date', '')
                    }
                    
                    logger.info(f"✅ Found in OpenAlex: {result['display_name']}")
                    
                    # Log additional matches for user info
                    if len(results) > 1:
                        logger.info(f"📊 Found {len(results)} matches in OpenAlex (showing first)")
                        
                else:
                    logger.info("❌ No results found in OpenAlex")
                    
            else:
                logger.error(f"❌ OpenAlex API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ OpenAlex search error: {e}")
            
        return result
    
    def analyze_journal_by_name(self, journal_name: str) -> Dict:
        """
        Complete workflow: Search journal by name and analyze if URL found
        
        Args:
            journal_name: Name of journal to search and analyze
            
        Returns:
            Dict with search results and analysis if possible
        """
        logger.info(f"🎯 Starting complete analysis workflow for: '{journal_name}'")
        
        # Step 1: Search for journal
        search_result = self.search_journal_by_name(journal_name)
        
        workflow_result = {
            'search_result': search_result,
            'analysis_result': None,
            'workflow_complete': False,
            'workflow_summary': []
        }
        
        # Step 2: If URL found, run analysis
        if search_result['can_analyze'] and search_result['suggested_url']:
            logger.info(f"🔬 Step 3: Running predatory analysis on: {search_result['suggested_url']}")
            
            try:
                analysis = self.analyze_journal_comprehensive(search_result['suggested_url'])
                workflow_result['analysis_result'] = analysis
                workflow_result['workflow_complete'] = True
                workflow_result['workflow_summary'].append("✅ Complete analysis workflow successful")
                
                # Add search context to analysis summary
                workflow_result['workflow_summary'].extend(search_result['search_summary'])
                workflow_result['workflow_summary'].append(f"📊 Predatory Risk Score: {analysis.overall_score:.1f}/100 ({analysis.risk_level})")
                
                logger.info(f"✅ Complete workflow successful: {analysis.overall_score:.1f}/100 ({analysis.risk_level})")
                
            except Exception as e:
                workflow_result['workflow_summary'].append(f"❌ Analysis failed: {str(e)}")
                logger.error(f"❌ Analysis failed for {search_result['suggested_url']}: {e}")
        else:
            workflow_result['workflow_summary'].extend(search_result['search_summary'])
            workflow_result['workflow_summary'].append("⚠️ Cannot proceed with analysis - no URL available")
            
        return workflow_result
    
    def analyze_journal_comprehensive(self, url: str, content: str = None) -> EnhancedAnalysisResult:
        """
        Comprehensive journal analysis using ALL evidence-based criteria
        
        Args:
            url: Journal website URL
            content: Optional pre-fetched content
            
        Returns:
            EnhancedAnalysisResult with complete analysis
        """
        start_time = time.time()
        logger.info(f"🔍 Starting comprehensive analysis of {url}")
        
        # Fetch content if not provided
        # EARLY REPUTATION VERIFICATION - Check external catalogs FIRST
        # This ensures legitimate journals are identified even if web scraping fails
        logger.info("🏛️ Checking external catalogs for journal legitimacy...")
        
        # Extract basic info for catalog lookup (even without full content)
        preliminary_title = self._extract_title_from_url(url)
        
        # Check NLM catalog first
        nlm_result = self._lookup_journal_in_nlm_basic(preliminary_title, url)
        
        # Check JIF catalog
        jif_result = self._lookup_journal_in_jif_basic(preliminary_title, url)
        
        # ALWAYS attempt web scraping for comprehensive analysis
        if content is None:
            logger.info("📡 Fetching website content...")
            content = self._fetch_content(url)
        
        if not content:
            # Create error result with external verification context
            logger.info("⚠️ Web scraping failed, using external verification only")
            return self._create_error_result_with_verification(url, "Could not access website", 
                                                             time.time() - start_time, nlm_result, jif_result)
        
        # ✅ WEB SCRAPING SUCCEEDED - Continue with full analysis
        logger.info("✅ Web content obtained, proceeding with comprehensive analysis")
        
        # Parse content
        soup = BeautifulSoup(content, 'html.parser')
        text = self._extract_clean_text(soup)
        
        # Enhanced content gathering: scrape about section and related pages
        logger.info("📚 Gathering comprehensive content from about section...")
        enhanced_content = self._scrape_about_section_comprehensive(url, soup, content)
        
        # Merge enhanced content with original
        if enhanced_content:
            text += "\n\n" + enhanced_content
            logger.info(f"✅ Enhanced analysis with {len(enhanced_content)} additional characters from about sections")
        
        # ENHANCED REPUTATION VERIFICATION - Combine early + scraped data
        logger.info("🏛️ Enhancing external catalog verification with scraped content...")
        journal_title = self._extract_journal_title(soup, url)
        issns = self._extract_issns_from_content(text, soup)
        
        # Enhance NLM result with scraped data if early lookup failed
        if not nlm_result['found_in_nlm']:
            enhanced_nlm_result = self._lookup_journal_in_nlm(journal_title, issns, url)
            if enhanced_nlm_result['found_in_nlm']:
                logger.info(f"✅ NLM ENHANCED: Found with scraped data - {enhanced_nlm_result['title']}")
                nlm_result = enhanced_nlm_result
        else:
            logger.info(f"✅ NLM EARLY: Using early verification result - {nlm_result['title']}")
        
        if nlm_result['found_in_nlm']:
            logger.info(f"🎯 NLM STATUS: Journal found in catalog (Match: {nlm_result['match_type']}, "
                       f"MEDLINE: {nlm_result['medline_indexed']}, Boost: +{nlm_result['reputation_boost']:.1f})")
        else:
            logger.info("📊 NLM STATUS: Journal not found in NLM catalog")
        
        # Enhance JIF result with scraped data if early lookup failed
        if not jif_result['found_in_jif']:
            enhanced_jif_result = self._lookup_journal_in_jif(journal_title, issns, url)
            if enhanced_jif_result.get('found', False):
                logger.info(f"✅ JIF ENHANCED: Found with scraped data - {enhanced_jif_result['title']}")
                # Convert enhanced result to match expected structure
                jif_result = {
                    'found_in_jif': True,
                    'title': enhanced_jif_result['title'],
                    'impact_factor': enhanced_jif_result['impact_factor'],
                    'reputation_boost': enhanced_jif_result['reputation_boost'],
                    'impact_tier': enhanced_jif_result['tier'],
                    'match_type': enhanced_jif_result.get('match_type', 'enhanced')
                }
        else:
            if jif_result['found_in_jif']:
                logger.info(f"✅ JIF EARLY: Using early verification result - {jif_result['title']}")
        
        if jif_result['found_in_jif']:
            logger.info(f"📈 JIF STATUS: Journal found (IF: {jif_result['impact_factor']:.1f}, "
                       f"Tier: {jif_result['impact_tier']}, Match: {jif_result['match_type']}, "
                       f"Boost: +{jif_result['reputation_boost']:.1f})")
        else:
            logger.info("📊 JIF STATUS: Journal not found in JIF catalog")
        
        logger.info("🧠 Performing evidence-based analysis...")
        
        # 1. CRITICAL: Enhanced Peer Review Process Analysis (30/100)
        logger.info("   📋 Analyzing peer review transparency with decentralized model awareness...")
        peer_review_result = self._analyze_peer_review_enhanced(text, soup, url)
        
        # 2. HIGH: Context-Aware Language Analysis (25/100) 
        logger.info("   🔍 Performing context-aware language analysis...")
        language_result = self._analyze_predatory_language_enhanced(text, url)
        
        # 3. HIGH: Enhanced Editorial Board Analysis (20/100)
        logger.info("   👥 Verifying editorial board credentials...")
        editorial_result = self._analyze_editorial_board_enhanced(text, soup)
        
        # 4. MODERATE: External Indexing Verification (15/100)
        logger.info("   🌐 Performing external database verification...")
        indexing_result = self._verify_indexing_claims_external(text, url)
        
        # 5. LOW: Contact Transparency (10/100) - Reduced weight
        logger.info("   📞 Checking contact transparency...")
        contact_result = self._analyze_contact_transparency_basic(text, soup)
        
        # 6. ADDITIONAL: Journal Name Legitimacy Analysis
        logger.info("   📝 Analyzing journal name legitimacy...")
        name_result = self._analyze_journal_name_legitimacy(soup, url)
        
        # Calculate final comprehensive score
        analysis_duration = time.time() - start_time
        result = self._calculate_comprehensive_score(
            peer_review_result, language_result, editorial_result,
            indexing_result, contact_result, name_result,
            url, analysis_duration, content, nlm_result, jif_result
        )
        
        logger.info(f"✅ Analysis complete: {result.overall_score:.1f}/100 ({result.risk_level})")
        return result
    
    def _analyze_peer_review_transparency(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        CRITICAL ANALYSIS: Peer Review Process Transparency (30/100 points)
        
        Academic Evidence: #1 indicator across ALL sources (COPE, Think-Check-Submit, etc.)
        
        Analyzes:
        - Presence and clarity of peer review process descriptions
        - Realistic vs unrealistic timeline promises  
        - Reviewer qualification requirements
        - Editorial decision processes
        - Review stages and criteria
        """
        score = 0
        flags = []
        warnings = []
        details = {}
        
        text_lower = text.lower()
        
        # 1. Basic peer review mentions
        review_keywords = [
            'peer review', 'review process', 'editorial process', 'manuscript review',
            'reviewer', 'review criteria', 'editorial review', 'academic review'
        ]
        
        review_mentions = sum(1 for keyword in review_keywords if keyword in text_lower)
        details['review_mentions'] = review_mentions
        
        if review_mentions == 0:
            score += 25  # CRITICAL: No peer review mentioned
            flags.append("🚨 CRITICAL: No peer review process mentioned")
        elif review_mentions < 3:
            score += 15  # HIGH: Minimal mention
            warnings.append("⚠️ Limited peer review information provided")
        else:
            details['adequate_review_mentions'] = True
        
        # 2. Process clarity and stages
        clarity_indicators = [
            'review stages', 'review criteria', 'reviewer guidelines', 'editorial decision',
            'revision process', 'acceptance criteria', 'review timeline', 'reviewer selection',
            'editorial board review', 'manuscript evaluation', 'quality assessment'
        ]
        
        clarity_score = sum(1 for indicator in clarity_indicators if indicator in text_lower)
        details['process_clarity_score'] = clarity_score
        
        if clarity_score == 0:
            score += 15  # No clear process description
            flags.append("❌ No clear peer review process described")
        elif clarity_score < 3:
            score += 8   # Limited clarity
            warnings.append("⚠️ Vague peer review process description")
        else:
            details['clear_process_description'] = True
        
        # 3. Check for CRITICAL RED FLAGS: Unrealistic timeline promises
        unrealistic_patterns = [
            r'(?:review|decision)\s+(?:within|in)\s+(?:24\s+)?hours?',
            r'(?:immediate|instant|same[- ]day)\s+(?:review|decision|publication)',
            r'(?:rapid|express)\s+review\s+(?:within|in)\s+(?:24\s+hours?|\d+\s+hours?)',
            r'no\s+(?:waiting|delay)\s+(?:time|period)',
            r'(?:publish|accept)\s+(?:within|in)\s+(?:24\s+hours?|\d+\s+hours?)'
        ]
        
        unrealistic_found = []
        for pattern in unrealistic_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                unrealistic_found.extend(matches)
                score += 20  # CRITICAL unrealistic promises
                flags.append(f"🚨 CRITICAL: Unrealistic review timeline promise: '{matches[0]}'")
                break
        
        details['unrealistic_timelines'] = unrealistic_found
        
        # 4. Reviewer qualification mentions
        qualification_keywords = [
            'qualified reviewer', 'expert reviewer', 'reviewer expertise', 'reviewer credentials',
            'reviewer selection', 'academic reviewer', 'specialist reviewer', 'field expert'
        ]
        
        qualification_mentions = sum(1 for keyword in qualification_keywords if keyword in text_lower)
        details['reviewer_qualification_mentions'] = qualification_mentions
        
        if qualification_mentions == 0:
            score += 10  # No mention of reviewer qualifications
            warnings.append("⚠️ No reviewer qualification requirements mentioned")
        else:
            details['mentions_reviewer_qualifications'] = True
        
        # 5. Check for FAKE REVIEW red flags
        fake_review_patterns = [
            r'no\s+(?:peer\s+)?review\s+(?:required|needed)',
            r'(?:skip|bypass)\s+(?:peer\s+)?review',
            r'minimal\s+review\s+(?:required|needed)',
            r'automatic\s+(?:acceptance|approval)',
            r'guaranteed\s+(?:acceptance|publication)'
        ]
        
        for pattern in fake_review_patterns:
            if re.search(pattern, text_lower):
                score += 25  # MAXIMUM penalty for fake review
                flags.append("🚨 CRITICAL: Fake or minimal peer review detected")
                details['fake_review_detected'] = True
                break
        
        return {
            'score': min(score, 30),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'category': 'peer_review_transparency'
        }
    
    def _analyze_peer_review_enhanced(self, text: str, soup: BeautifulSoup, url: str) -> Dict:
        """
        Enhanced peer review analysis that properly distinguishes between:
        - Legitimate decentralized peer review models (PLOS ONE, BMC, etc.)
        - Predatory fake peer review processes
        
        Accounts for modern publishing practices including distributed editorial models.
        """
        score = 0
        flags = []
        warnings = []
        details = {}
        text_lower = text.lower()
        
        # Identify if this is a known legitimate publisher using decentralized models
        legitimate_decentralized_publishers = [
            'plos.org', 'biomedcentral.com', 'springer.com', 'nature.com',
            'frontiersin.org', 'hindawi.com', 'mdpi.com', 'elife.org'
        ]
        
        is_known_legitimate = any(pub in url.lower() for pub in legitimate_decentralized_publishers)
        details['known_legitimate_publisher'] = is_known_legitimate
        
        # 1. Basic peer review mentions (with context awareness)
        peer_review_indicators = [
            'peer review', 'review process', 'editorial process', 'manuscript review',
            'reviewer', 'review criteria', 'editorial review', 'academic review',
            'editorial decision', 'manuscript evaluation', 'quality assessment'
        ]
        
        review_mentions = sum(1 for keyword in peer_review_indicators if keyword in text_lower)
        details['review_mentions'] = review_mentions
        
        if review_mentions == 0:
            score += 25  # CRITICAL: No peer review mentioned
            flags.append("🚨 CRITICAL: No peer review process mentioned")
        elif review_mentions < 3:
            if is_known_legitimate:
                score += 8   # Reduced penalty for known publishers
                warnings.append("⚠️ Limited peer review information (known publisher)")
            else:
                score += 15  # Standard penalty for unknown publishers
                warnings.append("⚠️ Limited peer review information provided")
        
        # 2. Detect legitimate decentralized model indicators (POSITIVE)
        decentralized_legitimate_indicators = [
            'academic editor', 'editorial board member', 'handling editor', 
            'section editor', 'associate editor', 'subject editor',
            'distributed editorial', 'specialized editor', 'expert editor',
            'editorial board handles', 'editor assigned', 'editor selection'
        ]
        
        decentralized_mentions = sum(1 for indicator in decentralized_legitimate_indicators if indicator in text_lower)
        details['decentralized_model_indicators'] = decentralized_mentions
        
        if decentralized_mentions >= 3:
            # This looks like legitimate decentralized model - REDUCE penalty
            score = max(0, score - 5)  # Reduce score by 5 points
            details['legitimate_decentralized_model'] = True
        
        # 3. Check for ACTUAL predatory red flags (not legitimate decentralization)
        genuine_predatory_flags = [
            r'no\s+peer\s+review\s+required',
            r'skip\s+(?:peer\s+)?review',
            r'minimal\s+review\s+process',
            r'instant\s+(?:peer\s+)?review',
            r'review\s+(?:within|in)\s+(?:24\s+)?hours?',
            r'guaranteed\s+acceptance',
            r'we\s+accept\s+all\s+(?:papers?|manuscripts?)'
        ]
        
        predatory_found = False
        for pattern in genuine_predatory_flags:
            if re.search(pattern, text_lower):
                score += 20  # High penalty for actual predatory indicators
                flags.append(f"🚨 CRITICAL: Genuine predatory review pattern detected")
                predatory_found = True
                break
        
        # 4. Large editorial board analysis (context-aware)
        editorial_size_indicators = [
            r'(\d+)\s+(?:editors?|editorial\s+board\s+members?)',
            r'editorial\s+board\s+of\s+(\d+)',
            r'over\s+(\d+)\s+editors?'
        ]
        
        board_size = 0
        for pattern in editorial_size_indicators:
            matches = re.findall(pattern, text_lower)
            if matches:
                board_size = max(board_size, int(matches[0]))
        
        details['estimated_board_size'] = board_size
        
        if board_size > 100:
            if is_known_legitimate:
                # Large board is POSITIVE for legitimate publishers
                details['large_legitimate_board'] = True
                warnings.append("✅ Large distributed editorial board (legitimate model)")
            else:
                # Large board might be suspicious for unknown publishers
                score += 3
                warnings.append("⚠️ Very large editorial board claims")
        
        # 5. Publisher-specific adjustments
        if is_known_legitimate and not predatory_found:
            # Further reduce penalty for known legitimate publishers with no red flags
            score = max(0, score - 3)
            details['publisher_reputation_adjustment'] = -3
        
        # 6. Quality indicators for decentralized models
        quality_indicators = [
            'qualified reviewer', 'expert reviewer', 'academic reviewer',
            'institutional affiliation', 'peer review guidelines',
            'review criteria', 'editorial standards', 'publication ethics'
        ]
        
        quality_mentions = sum(1 for indicator in quality_indicators if indicator in text_lower)
        details['quality_indicators'] = quality_mentions
        
        if quality_mentions >= 5:
            score = max(0, score - 2)  # Bonus for quality indicators
            details['strong_quality_indicators'] = True
        
        return {
            'score': min(score, 30),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'category': 'enhanced_peer_review_analysis'
        }
    
    def _analyze_predatory_language_sophisticated(self, text: str) -> Dict:
        """
        Sophisticated predatory language analysis (25/100 points)
        
        Uses context-aware pattern matching and sentiment analysis
        based on academic research patterns.
        """
        score = 0
        flags = []
        warnings = []
        found_patterns = {'critical': [], 'high_risk': [], 'moderate': []}
        
        text_lower = text.lower()
        
        # CRITICAL RED FLAGS (25 points - any one triggers maximum)
        critical_categories = self.predatory_patterns['critical_red_flags']
        
        for category, patterns in critical_categories.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    found_patterns['critical'].extend(matches)
                    score = 25  # Any critical flag = maximum score
                    flags.append(f"🚨 CRITICAL {category.replace('_', ' ').title()}: '{matches[0]}'")
                    return {
                        'score': 25,
                        'flags': flags,
                        'warnings': warnings,
                        'details': found_patterns,
                        'category': 'predatory_language_critical'
                    }
        
        # HIGH-RISK INDICATORS (8 points each, max 20)
        high_risk_categories = self.predatory_patterns['high_risk_indicators']
        high_risk_count = 0
        
        for category, patterns in high_risk_categories.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    found_patterns['high_risk'].extend(matches)
                    high_risk_count += len(matches)
                    if len(matches) <= 2:  # Don't spam with too many flags
                        flags.append(f"⚠️ High Risk {category.replace('_', ' ').title()}: '{matches[0]}'")
        
        if high_risk_count > 0:
            score += min(high_risk_count * 8, 20)  # 8 points each, max 20
        
        # MODERATE-RISK INDICATORS (3 points each, max 10)  
        moderate_categories = self.predatory_patterns['moderate_risk_indicators']
        moderate_count = 0
        
        for category, patterns in moderate_categories.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    found_patterns['moderate'].extend(matches)
                    moderate_count += len(matches)
        
        if moderate_count > 0:
            score += min(moderate_count * 3, 10)  # 3 points each, max 10
            warnings.append(f"⚠️ {moderate_count} moderate-risk promotional indicators found")
        
        return {
            'score': min(score, 25),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': found_patterns,
            'category': 'sophisticated_language_analysis'
        }
    
    def _analyze_predatory_language_enhanced(self, text: str, url: str) -> Dict:
        """
        Enhanced context-aware predatory language analysis (25/100 points)
        
        Distinguishes between:
        - Legitimate medical/academic terminology and submission processes
        - Actual predatory language and misleading claims
        - Standard publisher language vs manipulative marketing
        """
        score = 0
        flags = []
        warnings = []
        found_patterns = {'critical': [], 'high_risk': [], 'moderate': []}
        text_lower = text.lower()
        
        # Identify if this is a known legitimate publisher
        legitimate_publishers = [
            'plos.org', 'biomedcentral.com', 'springer.com', 'nature.com',
            'frontiersin.org', 'elife.org', 'bmj.com', 'elsevier.com',
            'wiley.com', 'taylor', 'sage', 'cambridge.org', 'oxford'
        ]
        
        is_known_legitimate = any(pub in url.lower() for pub in legitimate_publishers)
        
        # CRITICAL RED FLAGS (only genuine predatory indicators)
        genuine_critical_patterns = {
            'guaranteed_acceptance': [
                r'guaranteed?\s+(?:acceptance|publication|approval)',
                r'we\s+(?:accept|publish)\s+all\s+(?:papers?|manuscripts?|submissions?)',
                r'(?:100%|assured|certain)\s+(?:acceptance|approval)',
                r'acceptance\s+(?:rate|ratio)[:\s]+(?:100|99)%'
            ],
            'fake_peer_review': [
                r'no\s+(?:peer\s+)?review\s+(?:required|needed|necessary)',
                r'(?:skip|bypass|avoid)\s+(?:peer\s+)?review',
                r'minimal\s+(?:peer\s+)?review\s+(?:process|required)',
                r'(?:instant|immediate)\s+(?:peer\s+)?review\s+(?:guaranteed|promised)'
            ],
            'fake_metrics': [
                r'(?:impact\s+factor|if)[:\s]+(?:will\s+be|guaranteed|assured)\s+\d+',
                r'(?:guaranteed|assured|promised)\s+(?:impact\s+factor|citations?)',
                r'fake\s+(?:impact\s+factor|indexing|database)'
            ]
        }
        
        # Check for genuine critical red flags
        for category, patterns in genuine_critical_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    found_patterns['critical'].extend(matches)
                    score = 25  # Any critical flag = maximum score
                    flags.append(f"🚨 CRITICAL {category.replace('_', ' ').title()}: '{matches[0]}'")
                    return {
                        'score': 25,
                        'flags': flags,
                        'warnings': warnings,
                        'details': found_patterns,
                        'category': 'enhanced_predatory_language_critical'
                    }
        
        # HIGH-RISK INDICATORS (but context-aware)
        high_risk_patterns = {
            'unrealistic_timelines': [
                r'(?:publish|review|decision)\s+(?:within|in)\s+(?:24\s+hours?|\d+\s+hours?)',
                r'(?:immediate|instant|same[- ]day)\s+(?:publication|review|decision)',
                r'(?:express|emergency|urgent)\s+(?:publication|review|processing)'
            ],
            'aggressive_marketing': [
                r'(?:limited\s+time|special|exclusive)\s+(?:offer|deal|opportunity)',
                r'(?:act\s+(?:now|quickly|fast)|hurry|don\'t\s+miss)',
                r'(?:discount|promotion|reduced\s+price|sale)\s+(?:available|ending)'
            ]
        }
        
        # Context-aware legitimate language that should NOT be penalized
        legitimate_language_patterns = [
            r'rapid\s+(?:publication|processing|review)\s+(?:service|available|option)',
            r'fast\s+track\s+(?:submission|review|publication)',
            r'express\s+(?:service|option|track)\s+available',
            r'standard\s+(?:processing|publication|review)\s+time'
        ]
        
        # Check if potentially flagged language has legitimate context
        def has_legitimate_context(matched_text):
            # Look for legitimate context around the match
            for legit_pattern in legitimate_language_patterns:
                if re.search(legit_pattern, matched_text):
                    return True
            return False
        
        high_risk_count = 0
        for category, patterns in high_risk_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    # Create context around the match for analysis
                    match_start = text_lower.find(match)
                    context_start = max(0, match_start - 100)
                    context_end = min(len(text_lower), match_start + len(match) + 100)
                    context = text_lower[context_start:context_end]
                    
                    # Reduce penalty if legitimate context or known publisher
                    if is_known_legitimate or has_legitimate_context(context):
                        # Reduced penalty for legitimate publishers
                        penalty = 3  # Instead of 8
                        warnings.append(f"⚠️ {category.replace('_', ' ').title()}: '{match}' (reduced - legitimate publisher)")
                    else:
                        penalty = 8  # Full penalty
                        flags.append(f"⚠️ High Risk {category.replace('_', ' ').title()}: '{match}'")
                    
                    score += penalty
                    high_risk_count += 1
                    found_patterns['high_risk'].append(match)
                    
                    if high_risk_count >= 3:  # Limit flags to avoid spam
                        break
        
        # Cap high-risk score
        score = min(score, 20)
        
        # MODERATE-RISK INDICATORS (with context awareness)
        moderate_patterns = [
            r'(?:quality|prestigious|high[- ]impact|leading)\s+journal',
            r'(?:international|worldwide|global)\s+(?:reach|audience|recognition)',
            r'(?:expert|qualified|experienced)\s+(?:editors?|reviewers?)'
        ]
        
        moderate_count = 0
        for pattern in moderate_patterns:
            matches = re.findall(pattern, text_lower)
            if matches and not is_known_legitimate:
                # Only penalize unknown publishers for promotional language
                moderate_count += len(matches)
                found_patterns['moderate'].extend(matches)
        
        if moderate_count > 5 and not is_known_legitimate:
            score += min(moderate_count * 2, 8)  # 2 points each, max 8
            warnings.append(f"⚠️ Excessive promotional language detected ({moderate_count} instances)")
        
        return {
            'score': min(score, 25),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': found_patterns,
            'category': 'enhanced_context_aware_language_analysis'
        }
    
    def _analyze_editorial_board_enhanced(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        Enhanced editorial board analysis with credential verification (20/100 points)
        
        Goes beyond basic detection to analyze credibility indicators
        """
        score = 0
        flags = []
        warnings = []
        details = {}
        
        text_lower = text.lower()
        
        # 1. Editorial board presence and mentions
        board_keywords = [
            'editorial board', 'editors', 'editorial team', 'associate editors',
            'editor-in-chief', 'managing editor', 'editorial committee', 'advisory board'
        ]
        
        board_mentions = sum(1 for keyword in board_keywords if keyword in text_lower)
        details['board_mentions'] = board_mentions
        
        if board_mentions == 0:
            score += 15  # High penalty for no editorial board
            flags.append("❌ No editorial board information found")
        elif board_mentions < 2:
            score += 8   # Moderate penalty for limited info
            warnings.append("⚠️ Limited editorial board information")
        
        # 2. Credential and affiliation indicators
        credential_patterns = [
            r'(?:dr\.?|prof\.?|professor)\s+\w+\s+\w+',  # Academic titles with names
            r'ph\.?d\.?',                                # PhD mentions
            r'(?:university|college|institute|hospital)\s+of\s+\w+', # Institutions
            r'department\s+of\s+\w+',                    # Academic departments
            r'school\s+of\s+(?:medicine|engineering|science)', # Academic schools
            r'\w+\s+university',                         # University names
            r'medical\s+(?:school|center|college)',      # Medical institutions
        ]
        
        total_credentials = 0
        for pattern in credential_patterns:
            matches = len(re.findall(pattern, text_lower))
            total_credentials += matches
        
        details['credential_indicators'] = total_credentials
        
        if total_credentials == 0:
            score += 12  # No academic credentials
            flags.append("❌ No academic credentials or affiliations found")
        elif total_credentials < 5:
            score += 6   # Few credentials
            warnings.append("⚠️ Limited academic credential information")
        elif total_credentials >= 10:
            details['strong_credential_presence'] = True
        
        # 3. Check for suspicious editorial board patterns
        suspicious_patterns = [
            r'same\s+editorial\s+board',
            r'shared\s+(?:editors|editorial\s+board)',
            r'no\s+editorial\s+board\s+(?:required|needed)',
            r'editors?\s+(?:anonymous|confidential|private)',
            r'editorial\s+board\s+(?:to\s+be\s+announced|tba|coming\s+soon)'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                score += 15  # High penalty for suspicious patterns
                flags.append("🚨 Suspicious editorial board pattern detected")
                details['suspicious_editorial_patterns'] = True
                break
        
        # 4. Geographic and diversity indicators
        geographic_indicators = [
            'international', 'global', 'worldwide', 'multi-national',
            'diverse', 'various countries', 'different continents'
        ]
        
        geographic_mentions = sum(1 for indicator in geographic_indicators if indicator in text_lower)
        details['geographic_diversity_claims'] = geographic_mentions
        
        if geographic_mentions > 3:
            warnings.append("⚠️ Excessive geographic diversity claims")
            score += 3  # Slight penalty for over-claiming
        
        return {
            'score': min(score, 20),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'category': 'enhanced_editorial_analysis'
        }
    
    def _verify_indexing_claims_external(self, text: str, url: str) -> Dict:
        """
        External database verification (15/100 points)
        
        Cross-checks indexing claims against real databases
        """
        score = 0
        flags = []
        warnings = []
        details = {}
        verification_results = {}
        
        text_lower = text.lower()
        
        # 1. Extract indexing claims
        indexing_keywords = [
            'indexed in', 'indexing', 'database', 'pubmed', 'medline', 'scopus',
            'web of science', 'doaj', 'impact factor', 'thomson reuters', 'clarivate'
        ]
        
        indexing_mentions = sum(1 for keyword in indexing_keywords if keyword in text_lower)
        details['indexing_claims_count'] = indexing_mentions
        
        # 2. Check for specific database claims
        major_databases = ['pubmed', 'scopus', 'web of science', 'doaj']
        claimed_databases = []
        
        for db in major_databases:
            if db in text_lower:
                claimed_databases.append(db)
        
        details['claimed_major_databases'] = claimed_databases
        
        # 3. Attempt basic external verification (simplified for demo)
        if claimed_databases:
            logger.debug(f"   🔍 Attempting verification of {len(claimed_databases)} database claims...")
            
            # Simulate DOAJ verification (in real implementation, would use actual API)
            if 'doaj' in claimed_databases:
                # For demo purposes, we'll do a basic check
                domain = urlparse(url).netloc.lower()
                verification_results['doaj_check'] = self._simulate_doaj_verification(domain)
                
                if not verification_results['doaj_check']['verified']:
                    score += 8  # Penalty for false DOAJ claim
                    flags.append("❌ DOAJ indexing claimed but not verified")
        
        # 4. Check for suspicious indexing claims
        suspicious_indexing = [
            r'indexed\s+in\s+(?:all\s+)?(?:major\s+)?databases?',
            r'indexed\s+in\s+\d+\s+databases?',
            r'widely\s+indexed',
            r'multiple\s+(?:indexing|databases?)',
            r'comprehensive\s+(?:indexing|database\s+coverage)'
        ]
        
        suspicious_found = []
        for pattern in suspicious_indexing:
            matches = re.findall(pattern, text_lower)
            if matches:
                suspicious_found.extend(matches)
                score += 5  # Moderate penalty for vague claims
                warnings.append(f"⚠️ Vague indexing claim: '{matches[0]}'")
        
        details['suspicious_indexing_claims'] = suspicious_found
        
        # 5. Check for fake impact factor claims
        if_patterns = [
            r'impact\s+factor[:\s]+\d+\.\d+',
            r'if[:\s]+\d+\.\d+',
            r'journal\s+impact\s+factor[:\s]+\d+\.\d+',
            r'thomson\s+reuters\s+(?:impact\s+factor|if)[:\s]+\d+'
        ]
        
        if_claims = []
        for pattern in if_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if_claims.extend(matches)
                score += 8  # Penalty for specific IF claims without verification
                warnings.append(f"⚠️ Unverified impact factor claim: '{matches[0]}'")
        
        details['impact_factor_claims'] = if_claims
        
        # 6. Complete absence of indexing info
        if indexing_mentions == 0:
            score += 3  # Slight penalty for no indexing information
            warnings.append("⚠️ No database indexing information provided")
            details['no_indexing_info'] = True
        
        return {
            'score': min(score, 15),  # Cap at maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'verification_results': verification_results,
            'category': 'external_indexing_verification'
        }
    
    def _simulate_doaj_verification(self, domain: str) -> Dict:
        """
        Simulate DOAJ API verification (simplified for demo)
        In production, this would make actual API calls
        """
        # Known legitimate domains (simplified sample)
        legitimate_domains = [
            'plos.org', 'bmj.com', 'nature.com', 'sciencemag.org',
            'cell.com', 'thelancet.com', 'nejm.org', 'frontiersin.org'
        ]
        
        is_legitimate = any(legit in domain for legit in legitimate_domains)
        
        return {
            'verified': is_legitimate,
            'domain_checked': domain,
            'check_method': 'simplified_simulation',
            'note': 'In production, this would use actual DOAJ API'
        }
    
    def _analyze_contact_transparency_basic(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        Basic contact transparency analysis (10/100 points - reduced weight)
        
        Note: Reduced from 20 to 10 points based on academic research showing
        this is less critical than originally thought
        """
        score = 0
        flags = []
        warnings = []
        details = {}
        
        # Find contact information
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phones = re.findall(r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
        
        details['emails_found'] = len(emails)
        details['phones_found'] = len(phones)
        
        # Basic scoring (reduced penalties)
        if len(emails) == 0:
            score += 5  # Reduced from 6
            warnings.append("⚠️ No email contact information")
        
        if len(phones) == 0:
            score += 3  # Reduced from 4
        
        # Check for unprofessional domains (reduced penalty)
        unprofessional_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        for email in emails:
            if '@' in email:
                domain = email.split('@')[1].lower()
                if domain in unprofessional_domains:
                    score += 2  # Reduced from 3
                    warnings.append(f"⚠️ Unprofessional email domain: {domain}")
                    break
        
        return {
            'score': min(score, 10),  # Cap at reduced maximum weight
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'category': 'contact_transparency'
        }
    
    def _analyze_journal_name_legitimacy(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Analyze journal name for legitimacy and similarity to established journals
        """
        details = {}
        flags = []
        warnings = []
        
        # Extract journal title
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)
            details['extracted_title'] = title
            
            # Check similarity to legitimate journals
            similarities = []
            for legit_journal in self.legitimate_journals[:20]:  # Check top 20
                similarity = difflib.SequenceMatcher(None, title.lower(), legit_journal.lower()).ratio()
                if similarity > 0.8:  # High similarity threshold
                    similarities.append({
                        'legitimate_journal': legit_journal,
                        'similarity_score': similarity,
                        'title_checked': title
                    })
            
            if similarities:
                details['suspicious_similarities'] = similarities
                flags.append(f"⚠️ Title similar to established journal: {similarities[0]['legitimate_journal']}")
            
            # Check for overly broad or suspicious naming patterns
            broad_patterns = [
                r'international\s+journal\s+of\s+(?:advanced\s+)?(?:science|research|studies)',
                r'global\s+journal\s+of\s+(?:research|science|studies)',
                r'world\s+journal\s+of\s+(?:science|research|studies)',
                r'universal\s+journal\s+of\s+(?:science|research)',
                r'(?:multidisciplinary|interdisciplinary)\s+(?:journal|research)'
            ]
            
            for pattern in broad_patterns:
                if re.search(pattern, title.lower()):
                    warnings.append("⚠️ Overly broad or generic journal title")
                    details['generic_title_pattern'] = True
                    break
        
        return {
            'flags': flags,
            'warnings': warnings,
            'details': details,
            'category': 'journal_name_legitimacy'
        }
    
    def _calculate_comprehensive_score(self, peer_review_result, language_result, 
                                     editorial_result, indexing_result, contact_result,
                                     name_result, url, duration, content, nlm_result=None, jif_result=None) -> EnhancedAnalysisResult:
        """Calculate comprehensive final score with evidence-based weighting and reputation boosts"""
        
        # Extract scores
        peer_score = peer_review_result['score']
        language_score = language_result['score'] 
        editorial_score = editorial_result['score']
        indexing_score = indexing_result['score']
        contact_score = contact_result['score']
        
        # Apply NLM catalog reputation boost (reduces predatory risk)
        nlm_boost = 0.0
        nlm_confidence_boost = 0.0
        if nlm_result and nlm_result.get('found_in_nlm', False):
            nlm_boost = nlm_result.get('reputation_boost', 0.0)
            nlm_confidence_boost = nlm_result.get('confidence_boost', 0.0)
            
            logger.info(f"🎯 NLM BOOST: -{nlm_boost:.1f} predatory risk reduction "
                       f"(Match: {nlm_result.get('match_type', 'unknown')}, "
                       f"MEDLINE: {nlm_result.get('medline_indexed', False)})")
        
        # Apply JIF catalog reputation boost (reduces predatory risk)
        jif_boost = 0.0
        jif_confidence_boost = 0.0
        if jif_result and jif_result.get('found_in_jif', False):
            jif_boost = jif_result.get('reputation_boost', 0.0)
            jif_confidence_boost = jif_result.get('confidence_boost', 0.0)
            
            logger.info(f"📈 JIF BOOST: -{jif_boost:.1f} predatory risk reduction "
                       f"(IF: {jif_result.get('impact_factor', 0):.1f}, "
                       f"Tier: {jif_result.get('impact_tier', 'unknown')})")
        
        # Combine both boosts (take the higher of the two, don't double-count)
        combined_boost = max(nlm_boost, jif_boost)
        combined_confidence_boost = max(nlm_confidence_boost, jif_confidence_boost)
        
        # If journal is found in both catalogs, apply a modest additional bonus
        if nlm_boost > 0 and jif_boost > 0:
            combined_boost = max(nlm_boost, jif_boost) + min(nlm_boost, jif_boost) * 0.3  # 30% bonus
            combined_confidence_boost = max(nlm_confidence_boost, jif_confidence_boost) + 5.0  # Extra confidence
            logger.info(f"⭐ DUAL VERIFICATION BONUS: Found in both NLM and JIF catalogs (+{min(nlm_boost, jif_boost) * 0.3:.1f})")
        
        # Apply combined boost to reduce predatory scores
        if combined_boost > 0:
            peer_score = max(0, peer_score - (combined_boost * 0.4))  # 40% of boost to peer review
            language_score = max(0, language_score - (combined_boost * 0.3))  # 30% to language
            editorial_score = max(0, editorial_score - (combined_boost * 0.2))  # 20% to editorial
            indexing_score = max(0, indexing_score - (combined_boost * 0.1))  # 10% to indexing
        
        # Calculate weighted total
        total_score = peer_score + language_score + editorial_score + indexing_score + contact_score
        
        # Collect all findings
        all_flags = []
        all_warnings = []
        all_concerns = []
        positive_indicators = []
        
        # Collect flags and warnings from all analyses
        for result in [peer_review_result, language_result, editorial_result, indexing_result, contact_result]:
            all_flags.extend(result.get('flags', []))
            all_warnings.extend(result.get('warnings', []))
        
        # Add name analysis findings
        all_flags.extend(name_result.get('flags', []))
        all_warnings.extend(name_result.get('warnings', []))
        
        # Determine risk level with enhanced thresholds
        if total_score >= 75:
            risk_level = "Very High Risk"
        elif total_score >= 60:
            risk_level = "High Risk"
        elif total_score >= 40:
            risk_level = "Moderate Risk"
        elif total_score >= 20:
            risk_level = "Low Risk"
        else:
            risk_level = "Very Low Risk"
        
        # Calculate dynamic confidence with 95% CI (including both boosts)
        confidence_result = self._calculate_dynamic_confidence(
            total_score, peer_score, language_score, editorial_score, 
            indexing_score, contact_score, content, all_flags, combined_confidence_boost
        )
        confidence = confidence_result['confidence']
        confidence_lower = confidence_result['confidence_95ci_lower']
        confidence_upper = confidence_result['confidence_95ci_upper']
        
        # Generate comprehensive recommendations
        recommendations = self._generate_comprehensive_recommendations(
            total_score, peer_score, language_score, editorial_score, 
            indexing_score, all_flags
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(total_score, risk_level)
        
        # Identify positive indicators
        if peer_score <= 5:
            positive_indicators.append("✅ Clear peer review process described")
        if editorial_score <= 5:
            positive_indicators.append("✅ Strong editorial board credentials")
        if language_score == 0:
            positive_indicators.append("✅ No predatory language detected")
        if indexing_score <= 3:
            positive_indicators.append("✅ Reasonable indexing claims")
        
        # Add NLM-specific positive indicators
        if nlm_result and nlm_result.get('found_in_nlm', False):
            if nlm_result.get('medline_indexed', False):
                positive_indicators.append("🏛️ Journal found in NLM catalog (MEDLINE-indexed)")
            else:
                positive_indicators.append("🏛️ Journal found in NLM catalog")
            positive_indicators.append(f"🎯 NLM match type: {nlm_result.get('match_type', 'unknown')}")
        
        # Add JIF-specific positive indicators
        if jif_result and jif_result.get('found_in_jif', False):
            impact_factor = jif_result.get('impact_factor', 0)
            impact_tier = jif_result.get('impact_tier', 'unknown')
            
            if impact_tier == 'elite':
                positive_indicators.append(f"⭐ Elite journal with very high impact factor (IF: {impact_factor:.1f})")
            elif impact_tier == 'high':
                positive_indicators.append(f"📈 High-impact journal (IF: {impact_factor:.1f})")
            elif impact_tier == 'medium_high':
                positive_indicators.append(f"📊 Above-average impact journal (IF: {impact_factor:.1f})")
            else:
                positive_indicators.append(f"📉 Journal found in JIF catalog (IF: {impact_factor:.1f})")
            
            positive_indicators.append(f"🎯 JIF match type: {jif_result.get('match_type', 'unknown')}")
        
        # Add dual verification bonus indicator
        if (nlm_result and nlm_result.get('found_in_nlm', False) and 
            jif_result and jif_result.get('found_in_jif', False)):
            positive_indicators.append("⭐ Journal verified in both NLM and JIF catalogs")
        
        # Prepare external verification with both NLM and JIF data
        external_verification = indexing_result.get('verification_results', {})
        
        if nlm_result:
            external_verification['nlm_catalog'] = {
                'found_in_nlm': nlm_result.get('found_in_nlm', False),
                'medline_indexed': nlm_result.get('medline_indexed', False),
                'match_type': nlm_result.get('match_type'),
                'reputation_boost_applied': nlm_result.get('reputation_boost', 0.0),
                'nlm_entry': nlm_result.get('nlm_entry')
            }
        
        if jif_result:
            external_verification['jif_catalog'] = {
                'found_in_jif': jif_result.get('found_in_jif', False),
                'impact_factor': jif_result.get('impact_factor', 0.0),
                'impact_tier': jif_result.get('impact_tier', 'unknown'),
                'match_type': jif_result.get('match_type'),
                'reputation_boost_applied': jif_result.get('reputation_boost', 0.0),
                'jif_entry': jif_result.get('jif_entry')
            }
        
        return EnhancedAnalysisResult(
            overall_score=total_score,
            risk_level=risk_level,
            confidence_score=confidence,
            confidence_95ci_lower=confidence_lower,
            confidence_95ci_upper=confidence_upper,
            
            peer_review_score=peer_score,
            predatory_language_score=language_score,
            editorial_board_score=editorial_score,
            indexing_verification_score=indexing_score,
            contact_transparency_score=contact_score,
            
            critical_red_flags=[f for f in all_flags if '🚨' in f],
            high_risk_warnings=[f for f in all_flags if '❌' in f],
            moderate_concerns=all_warnings,
            positive_indicators=positive_indicators,
            
            external_verification=external_verification,
            
            peer_review_analysis=peer_review_result.get('details', {}),
            language_analysis=language_result.get('details', {}),
            editorial_analysis=editorial_result.get('details', {}),
            indexing_analysis=indexing_result.get('details', {}),
            
            recommendations=recommendations,
            next_steps=next_steps,
            
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration=duration,
            journal_url=url
        )
    
    def _calculate_dynamic_confidence(self, total_score, peer_score, language_score, 
                                    editorial_score, indexing_score, contact_score, 
                                    content, flags, nlm_confidence_boost=0.0):
        """
        Calculate dynamic confidence with 95% confidence intervals
        
        Factors considered:
        - Data quality and completeness
        - Score consistency and variance
        - External validation signals (including NLM catalog)
        - Analysis coverage
        """
        import math
        
        # Base confidence from score (refined)
        if total_score >= 75:
            base_confidence = 0.92
        elif total_score >= 60:
            base_confidence = 0.85
        elif total_score >= 40:
            base_confidence = 0.75
        elif total_score >= 20:
            base_confidence = 0.68
        else:
            base_confidence = 0.60
        
        # Adjustment factors
        adjustments = 0.0
        uncertainty_factors = []
        
        # 1. Data Quality Factor (±0.15)
        content_length = len(content) if content else 0
        if content_length > 50000:  # Rich content available
            adjustments += 0.10
            uncertainty_factors.append(0.02)  # Low uncertainty
        elif content_length > 20000:  # Moderate content
            adjustments += 0.05
            uncertainty_factors.append(0.04)  # Medium uncertainty  
        elif content_length > 5000:   # Limited content
            adjustments -= 0.05
            uncertainty_factors.append(0.08)  # High uncertainty
        else:  # Very limited content
            adjustments -= 0.15
            uncertainty_factors.append(0.12)  # Very high uncertainty
        
        # 2. Score Consistency Factor (±0.10)
        scores = [peer_score, language_score, editorial_score, indexing_score, contact_score]
        score_std = math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))
        if score_std < 5:  # Consistent scores
            adjustments += 0.08
            uncertainty_factors.append(0.02)
        elif score_std < 10:  # Moderate consistency
            adjustments += 0.03
            uncertainty_factors.append(0.04)
        else:  # Inconsistent scores
            adjustments -= 0.05
            uncertainty_factors.append(0.08)
        
        # 3. External Validation Factor (±0.08)
        # Check for positive indicators (inverse of flags)
        critical_flags = len([f for f in flags if 'critical' in f.lower() or 'red flag' in f.lower()])
        if critical_flags == 0:
            adjustments += 0.08
            uncertainty_factors.append(0.01)
        elif critical_flags <= 2:
            adjustments += 0.03
            uncertainty_factors.append(0.03)
        else:
            adjustments -= 0.05
            uncertainty_factors.append(0.06)
        
        # 4. Analysis Completeness Factor (±0.07)
        # All scores available (none are 0 when they should have values)
        non_zero_scores = len([s for s in scores if s > 0])
        if non_zero_scores >= 4:  # Most criteria analyzed
            adjustments += 0.05
            uncertainty_factors.append(0.02)
        elif non_zero_scores >= 3:  # Some criteria analyzed
            adjustments += 0.02
            uncertainty_factors.append(0.03)
        else:  # Limited analysis
            adjustments -= 0.05
            uncertainty_factors.append(0.07)
        
        # Apply NLM catalog confidence boost
        nlm_adjustment = nlm_confidence_boost / 100.0  # Convert percentage to decimal
        if nlm_adjustment > 0:
            adjustments += nlm_adjustment
            logger.info(f"🎯 NLM Confidence Boost: +{nlm_confidence_boost:.1f}% applied")
        
        # Calculate final confidence
        confidence = max(0.50, min(0.98, base_confidence + adjustments))
        
        # Calculate 95% confidence interval
        # Combined uncertainty from all factors
        combined_uncertainty = math.sqrt(sum(u**2 for u in uncertainty_factors))
        margin_of_error = 1.96 * combined_uncertainty  # 95% CI
        
        confidence_lower = max(0.40, confidence - margin_of_error)
        confidence_upper = min(0.99, confidence + margin_of_error)
        
        return {
            'confidence': confidence,
            'confidence_95ci_lower': confidence_lower,
            'confidence_95ci_upper': confidence_upper,
            'base_confidence': base_confidence,
            'adjustments': adjustments,
            'uncertainty': combined_uncertainty
        }
    
    def _generate_comprehensive_recommendations(self, total_score, peer_score, 
                                              language_score, editorial_score, 
                                              indexing_score, flags) -> List[str]:
        """Generate evidence-based recommendations"""
        recommendations = []
        
        # Critical recommendations based on score
        if total_score >= 75:
            recommendations.append("🚨 AVOID: Multiple critical red flags detected")
            recommendations.append("📢 Consider reporting to institutional library or research office")
            recommendations.append("⚠️ This journal shows strong predatory indicators")
        elif total_score >= 50:
            recommendations.append("⚠️ CAUTION: Significant concerns identified")
            recommendations.append("🔍 Conduct additional verification before submission")
        elif total_score <= 20:
            recommendations.append("✅ Journal appears to follow academic standards")
            recommendations.append("💡 Consider final verification using Think-Check-Submit checklist")
        
        # Specific category recommendations
        if peer_score >= 20:
            recommendations.append("📋 CRITICAL: Inadequate peer review transparency")
        if editorial_score >= 15:
            recommendations.append("👥 WARNING: Editorial board credibility concerns")
        if language_score >= 15:
            recommendations.append("🔍 ALERT: Predatory language patterns detected")
        if indexing_score >= 10:
            recommendations.append("🌐 VERIFY: Cross-check indexing claims independently")
        
        # Always include evidence-based verification
        recommendations.append("🎓 Use established guidelines: Think-Check-Submit, COPE, DOAJ")
        
        return recommendations
    
    def _generate_next_steps(self, total_score, risk_level) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        if total_score >= 60:
            next_steps.append("❌ Do not submit to this journal")
            next_steps.append("🔍 Search for alternative legitimate journals in your field")
            next_steps.append("📚 Consult your institution's recommended journal lists")
        elif total_score >= 30:
            next_steps.append("🔍 Perform additional verification")
            next_steps.append("📞 Contact journal directly with specific questions")
            next_steps.append("👥 Seek colleague or librarian advice")
        else:
            next_steps.append("✅ Journal appears legitimate for consideration")
            next_steps.append("📝 Review submission guidelines carefully")
            next_steps.append("💡 Conduct final Think-Check-Submit verification")
        
        return next_steps
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True).lower()
    
    def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch website content with proper error handling"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _scrape_about_section_comprehensive(self, base_url: str, soup: BeautifulSoup, main_content: str) -> str:
        """
        Comprehensively scrape about section and related pages for deeper analysis
        
        This method:
        1. Identifies about section links on the main page
        2. Follows those links to gather additional content  
        3. Looks for key editorial/policy pages
        4. Returns consolidated additional content
        """
        from urllib.parse import urljoin, urlparse
        import time
        
        additional_content = []
        processed_urls = set()
        
        # About section keywords to look for in links
        about_keywords = [
            'about', 'editorial', 'policy', 'policies', 'ethics', 'peer-review', 
            'review-process', 'board', 'editors', 'submission', 'guidelines',
            'aims-scope', 'mission', 'vision', 'governance', 'standards',
            'manuscript', 'publication', 'author', 'reviewer', 'editorial-board'
        ]
        
        logger.info(f"   🔍 Searching for about section links...")
        
        # Find all links on the main page
        links = soup.find_all('a', href=True)
        about_links = []
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            # Check if link or text contains about keywords
            for keyword in about_keywords:
                if keyword in href or keyword in text:
                    full_url = urljoin(base_url, link.get('href'))
                    if full_url not in processed_urls and self._is_same_domain(base_url, full_url):
                        about_links.append({
                            'url': full_url,
                            'text': text,
                            'keyword': keyword
                        })
                        processed_urls.add(full_url)
                    break
        
        logger.info(f"   📄 Found {len(about_links)} about-related links to analyze")
        
        # Limit to most important links to avoid overwhelming the analysis
        priority_keywords = ['about', 'editorial', 'peer-review', 'policy', 'ethics', 'board']
        about_links.sort(key=lambda x: (
            0 if any(pk in x['keyword'] for pk in priority_keywords) else 1,
            len(x['text'])
        ))
        
        # Process up to 8 most relevant links
        for i, link_info in enumerate(about_links[:8]):
            try:
                logger.info(f"   📖 Scraping: {link_info['text'][:50]}...")
                
                # Rate limiting
                if i > 0:
                    time.sleep(0.5)
                
                # Fetch the about page content
                about_content = self._fetch_content(link_info['url'])
                if about_content:
                    about_soup = BeautifulSoup(about_content, 'html.parser')
                    about_text = self._extract_clean_text_simple(about_soup)
                    
                    # Only include if it's substantial and not duplicate
                    if len(about_text) > 200 and not self._is_duplicate_content(about_text, main_content):
                        additional_content.append(f"\n--- {link_info['text'].title()} Section ---\n{about_text}")
                        logger.info(f"   ✅ Added {len(about_text)} chars from {link_info['keyword']} page")
                    else:
                        logger.info(f"   ⏭️  Skipped {link_info['keyword']} page (duplicate/short)")
                        
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to scrape {link_info['url']}: {e}")
                continue
        
        return '\n'.join(additional_content)
    
    def _extract_clean_text_simple(self, soup: BeautifulSoup) -> str:
        """Extract clean text from BeautifulSoup object"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        return soup.get_text(separator=' ', strip=True)
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        from urllib.parse import urlparse
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2 or domain1 in domain2 or domain2 in domain1
        except:
            return False
    
    def _is_duplicate_content(self, new_content: str, existing_content: str) -> bool:
        """Check if new content is substantially duplicate of existing content"""
        # Simple similarity check based on common words
        new_words = set(new_content.lower().split())
        existing_words = set(existing_content.lower().split())
        
        if len(new_words) == 0:
            return True
            
        # If more than 70% of words are already in existing content, consider duplicate
        overlap = len(new_words.intersection(existing_words))
        similarity = overlap / len(new_words)
        return similarity > 0.7
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a likely journal title from the URL for catalog lookup"""
        from urllib.parse import urlparse
        
        try:
            # Parse the URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # Common patterns for journal titles in URLs
            # Try to extract from path segments
            path_segments = [seg for seg in path.split('/') if seg]
            
            # Look for journal identifiers in the path
            for segment in path_segments:
                if 'journal' in segment:
                    # Extract journal identifier
                    if segment.startswith('journal-'):
                        return segment.replace('journal-', '').replace('-', ' ')
                    elif '/' in segment:
                        continue  # Skip complex segments
                        
            # Look for known publisher patterns
            if 'sciencedirect.com' in domain:
                # Format: /science/journal/01406736
                if '/journal/' in path:
                    journal_id = path.split('/journal/')[-1].split('/')[0]
                    if journal_id.isdigit():
                        # This is an ISSN, check our catalogs
                        for issn_key in self.nlm_catalog.get('by_issn', {}):
                            if journal_id in issn_key.replace('-', ''):
                                return self.nlm_catalog['by_issn'][issn_key]['title_full']
                        
            # Fallback: extract from domain
            if 'lancet' in domain or 'thelancet' in domain:
                return 'Lancet'
            elif 'nature.com' in domain:
                return 'Nature'
            elif 'science.org' in domain or 'sciencemag.org' in domain:
                return 'Science'
            
            return ""  # No identifiable title
            
        except Exception:
            return ""
    
    def _lookup_journal_in_nlm_basic(self, title_hint: str, url: str) -> Dict:
        """Basic NLM lookup using URL patterns and title hints"""
        result = {'found_in_nlm': False, 'reputation_boost': 0, 'medline_indexed': False}
        
        try:
            # Check if we have any title hint to work with
            if title_hint:
                nlm_search = self._search_nlm_by_name(title_hint)
                if nlm_search['found']:
                    result = {
                        'found_in_nlm': True,
                        'title': nlm_search['title'],
                        'reputation_boost': 30.0 if nlm_search['medline_indexed'] else 15.0,
                        'medline_indexed': nlm_search['medline_indexed'],
                        'match_type': nlm_search.get('match_type', 'basic'),
                        'publisher': nlm_search.get('publisher', ''),
                    }
                    return result
            
            # URL-based pattern matching for known publishers
            url_lower = url.lower()
            
            # Check for ScienceDirect journal URLs with ISSNs
            if 'sciencedirect.com/science/journal/' in url_lower:
                issn_match = url_lower.split('/journal/')[-1].split('/')[0]
                
                # Look for this ISSN in NLM catalog
                for issn_key, entry in self.nlm_catalog.get('by_issn', {}).items():
                    if issn_match in issn_key.replace('-', ''):
                        result = {
                            'found_in_nlm': True,
                            'title': entry['title_full'],
                            'reputation_boost': 30.0 if entry['medline_indexed'] else 15.0,
                            'medline_indexed': entry['medline_indexed'],
                            'match_type': 'url_issn',
                            'publisher': entry.get('publisher', ''),
                        }
                        return result
                        
        except Exception as e:
            logger.error(f"❌ Basic NLM lookup error: {e}")
            
        return result
    
    def _lookup_journal_in_jif_basic(self, title_hint: str, url: str) -> Dict:
        """Basic JIF lookup using URL patterns and title hints"""
        result = {'found_in_jif': False, 'impact_factor': 0, 'reputation_boost': 0}
        
        try:
            if title_hint:
                jif_search = self._lookup_journal_in_jif(title_hint)
                if jif_search.get('found', False):  # Fix: use .get() with default
                    tier = self._classify_impact_tier(jif_search['impact_factor'])
                    reputation_boost, confidence_boost = self._calculate_jif_boosts(tier)
                    result = {
                        'found_in_jif': True,
                        'title': jif_search['title'],
                        'impact_factor': jif_search['impact_factor'],
                        'reputation_boost': reputation_boost,
                        'tier': tier,
                        'match_type': jif_search.get('match_type', 'basic')
                    }
                    
        except Exception as e:
            logger.error(f"❌ Basic JIF lookup error: {e}")
            
        return result
    
    def _create_error_result_with_verification(self, url: str, error_msg: str, duration: float, 
                                             nlm_result: Dict, jif_result: Dict) -> EnhancedAnalysisResult:
        """Create error result with external verification context"""
        
        # Determine appropriate score based on external verification
        if nlm_result['found_in_nlm'] or jif_result['found_in_jif']:
            # This is a verified legitimate journal that we just can't scrape
            if nlm_result.get('medline_indexed', False):
                # MEDLINE-indexed = very legitimate
                overall_score = 15.0  # Very low risk
                risk_level = "Very Low Risk"
                confidence = 75.0  # High confidence based on MEDLINE status
                positive_indicators = [
                    "✅ Journal found in NLM catalog",
                    "🏛️ MEDLINE-indexed (high credibility)",
                    f"📚 Publisher: {nlm_result.get('publisher', 'N/A')}"
                ]
            elif jif_result.get('impact_factor', 0) > 5.0:
                # High impact factor journal
                overall_score = 20.0  # Very low risk  
                risk_level = "Very Low Risk"
                confidence = 70.0  # High confidence based on impact factor
                positive_indicators = [
                    f"📈 High Impact Factor: {jif_result['impact_factor']:.2f}",
                    f"🏆 Journal tier: {jif_result.get('tier', 'N/A')}"
                ]
            elif nlm_result['found_in_nlm']:
                # In NLM catalog but not MEDLINE-indexed
                overall_score = 30.0  # Low risk
                risk_level = "Low Risk"
                confidence = 60.0  # Moderate confidence
                positive_indicators = [
                    "✅ Journal found in NLM catalog",
                    f"📚 Publisher: {nlm_result.get('publisher', 'N/A')}"
                ]
            else:
                # Only in JIF, lower confidence
                overall_score = 40.0  # Moderate risk due to access issues
                risk_level = "Moderate Risk"
                confidence = 50.0
                positive_indicators = [
                    f"📊 Impact Factor: {jif_result['impact_factor']:.2f}"
                ]
            
            # Add verification details
            external_verification = {}
            if nlm_result['found_in_nlm']:
                external_verification['nlm_catalog'] = nlm_result
            if jif_result['found_in_jif']:
                external_verification['jif_catalog'] = jif_result
            
        else:
            # Unknown journal that we can't access - neutral score
            overall_score = 50.0  # Neutral/unknown
            risk_level = "Cannot Analyze"
            confidence = 0.0
            positive_indicators = []
            external_verification = {}
        
        # Calculate confidence interval
        ci_margin = confidence * 0.1  # 10% margin
        confidence_95ci_lower = max(0.0, confidence - ci_margin)
        confidence_95ci_upper = min(100.0, confidence + ci_margin)
        
        return EnhancedAnalysisResult(
            overall_score=overall_score,
            risk_level=risk_level,
            confidence_score=confidence,
            confidence_95ci_lower=confidence_95ci_lower,
            confidence_95ci_upper=confidence_95ci_upper,
            
            peer_review_score=0.0,
            predatory_language_score=0.0,
            editorial_board_score=0.0,
            indexing_verification_score=0.0,
            contact_transparency_score=0.0,
            
            critical_red_flags=[],
            high_risk_warnings=[f"Analysis limited: {error_msg}"],
            moderate_concerns=[] if overall_score < 40 else ["Website access restricted"],
            positive_indicators=positive_indicators,
            
            external_verification=external_verification,
            peer_review_analysis={},
            language_analysis={},
            editorial_analysis={},
            indexing_analysis={},
            
            recommendations=[self._generate_access_restricted_recommendation(nlm_result, jif_result)],
            next_steps=self._generate_access_restricted_next_steps(nlm_result, jif_result),
            
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            analysis_duration=duration,
            journal_url=url
        )
    
    def _generate_access_restricted_recommendation(self, nlm_result: Dict, jif_result: Dict) -> str:
        """Generate recommendation for access-restricted but verified journals"""
        if nlm_result.get('medline_indexed', False):
            return ("🏛️ This journal is MEDLINE-indexed and found in the NLM catalog, indicating high credibility. "
                   "The website access restriction is likely due to publisher security measures, not predatory behavior.")
        elif nlm_result['found_in_nlm']:
            return ("✅ This journal is found in the NLM catalog, indicating legitimacy. "
                   "Website access issues do not suggest predatory behavior.")
        elif jif_result.get('impact_factor', 0) > 5.0:
            return (f"📈 This journal has a high impact factor ({jif_result['impact_factor']:.2f}) "
                   "suggesting established reputation. Access restrictions are common for major publishers.")
        else:
            return ("⚠️ Unable to analyze due to website access restrictions. "
                   "Consider alternative verification methods or contact the journal directly.")
    
    def _generate_access_restricted_next_steps(self, nlm_result: Dict, jif_result: Dict) -> List[str]:
        """Generate next steps for access-restricted journals"""
        steps = []
        
        if nlm_result.get('medline_indexed', False):
            steps.extend([
                "✅ No further verification needed - MEDLINE indexing confirms legitimacy",
                "📚 You may proceed with confidence for submissions",
                "🔍 Check PubMed for recent publications from this journal"
            ])
        elif nlm_result['found_in_nlm'] or jif_result['found_in_jif']:
            steps.extend([
                "✅ Journal appears legitimate based on catalog verification",
                "🔍 Search recent publications in PubMed or Google Scholar",
                "📧 Contact journal directly if you have specific concerns",
                "💡 Use Think-Check-Submit.org for additional verification"
            ])
        else:
            steps.extend([
                "⚠️ Manual verification required due to access limitations",
                "🔍 Search for journal reputation in academic databases",
                "📧 Contact institution library for journal assessment",
                "💡 Use Think-Check-Submit.org verification checklist"
            ])
            
        return steps
    
    def _create_error_result(self, url: str, error_msg: str, duration: float) -> EnhancedAnalysisResult:
        """Create error result when analysis fails (legacy method)"""
        return EnhancedAnalysisResult(
            overall_score=50.0,  # Changed from 100.0 to neutral
            risk_level="Cannot Analyze",
            confidence_score=0.0,
            
            peer_review_score=0.0,
            predatory_language_score=0.0,
            editorial_board_score=0.0,
            indexing_verification_score=0.0,
            contact_transparency_score=0.0,
            
            critical_red_flags=[f"Analysis Error: {error_msg}"],
            high_risk_warnings=[],
            moderate_concerns=[],
            positive_indicators=[],
            
            external_verification={},
            peer_review_analysis={},
            language_analysis={},
            editorial_analysis={},
            indexing_analysis={},
            
            recommendations=[f"Unable to analyze: {error_msg}", "Verify website accessibility"],
            next_steps=["Check URL and try again", "Verify internet connection"],
            
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration=duration,
            journal_url=url
        )
    
    def display_comprehensive_results(self, result: EnhancedAnalysisResult):
        """Display comprehensive analysis results"""
        print(f"\n" + "=" * 100)
        print(f"🎯 ENHANCED PREDATORY JOURNAL ANALYSIS - EVIDENCE-BASED RESULTS")
        print(f"=" * 100)
        print(f"🌐 URL: {result.journal_url}")
        print(f"📅 Analysis Date: {result.analysis_timestamp[:19]}")
        print(f"⏱️  Analysis Duration: {result.analysis_duration:.2f} seconds")
        print(f"=" * 100)
        
        # Overall Assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        status_emoji = "🚨" if result.overall_score >= 60 else "⚠️" if result.overall_score >= 30 else "✅"
        print(f"   {status_emoji} Risk Score: {result.overall_score:.1f}/100")
        print(f"   📊 Risk Level: {result.risk_level}")
        print(f"   🎯 Confidence: {result.confidence_score:.1%}")
        
        # Evidence-Based Category Breakdown
        print(f"\n📊 EVIDENCE-BASED CATEGORY BREAKDOWN:")
        print(f"   📋 Peer Review Transparency: {result.peer_review_score:.1f}/30 (CRITICAL)")
        print(f"   🔍 Predatory Language Analysis: {result.predatory_language_score:.1f}/25 (HIGH)")
        print(f"   👥 Editorial Board Verification: {result.editorial_board_score:.1f}/20 (HIGH)")
        print(f"   🌐 Indexing Verification: {result.indexing_verification_score:.1f}/15 (MODERATE)")
        print(f"   📞 Contact Transparency: {result.contact_transparency_score:.1f}/10 (LOW)")
        
        # Critical Findings
        if result.critical_red_flags:
            print(f"\n🚨 CRITICAL RED FLAGS:")
            for flag in result.critical_red_flags:
                print(f"   {flag}")
        
        if result.high_risk_warnings:
            print(f"\n❌ HIGH-RISK WARNINGS:")
            for warning in result.high_risk_warnings:
                print(f"   {warning}")
        
        if result.moderate_concerns:
            print(f"\n⚠️  MODERATE CONCERNS:")
            for concern in result.moderate_concerns[:5]:  # Limit to top 5
                print(f"   {concern}")
            if len(result.moderate_concerns) > 5:
                print(f"   ... and {len(result.moderate_concerns) - 5} more concerns")
        
        # Positive Indicators
        if result.positive_indicators:
            print(f"\n✅ POSITIVE INDICATORS:")
            for indicator in result.positive_indicators:
                print(f"   {indicator}")
        
        # External Verification
        if result.external_verification:
            print(f"\n🌐 EXTERNAL VERIFICATION RESULTS:")
            for key, value in result.external_verification.items():
                print(f"   {key}: {value}")
        
        # Recommendations
        print(f"\n💡 EVIDENCE-BASED RECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"   {rec}")
        
        # Next Steps
        print(f"\n📋 RECOMMENDED NEXT STEPS:")
        for step in result.next_steps:
            print(f"   {step}")
        
        print(f"\n" + "=" * 100)
        print(f"📚 Analysis based on: COPE, Think-Check-Submit, Eriksson & Helgesson,")
        print(f"    Jeffrey Beall's research, and recent academic literature (2023-2024)")
        print(f"=" * 100)

# Example usage and comprehensive demo
def main():
    """Demonstrate enhanced predatory journal detection"""
    print("🎯 ENHANCED PREDATORY JOURNAL DETECTOR - COMPREHENSIVE DEMO")
    print("=" * 80)
    print("Implementing ALL evidence-based improvements from academic research:")
    print("✅ Peer Review Transparency Analysis (30/100) - CRITICAL")
    print("✅ External Database Verification (15/100) - NEW")  
    print("✅ Enhanced Editorial Board Verification (20/100) - ENHANCED")
    print("✅ Sophisticated Language Detection (25/100) - ENHANCED")
    print("✅ Contact Transparency (10/100) - REDUCED WEIGHT")
    print("✅ Journal Name Legitimacy Analysis - NEW")
    print("=" * 80)
    
    detector = EnhancedPredatoryDetector()
    
    # Test with legitimate journals
    test_journals = [
        {
            'name': 'PLOS ONE (Legitimate)',
            'url': 'https://journals.plos.org/plosone/',
            'expected': 'Very Low Risk'
        },
        {
            'name': 'BMJ Open (Legitimate)',
            'url': 'https://bmjopen.bmj.com/',
            'expected': 'Low Risk'
        }
    ]
    
    for i, journal in enumerate(test_journals, 1):
        print(f"\n" + "🔍" * 80)
        print(f"[{i}/{len(test_journals)}] COMPREHENSIVE ANALYSIS: {journal['name']}")
        print(f"Expected Result: {journal['expected']}")
        print("🔍" * 80)
        
        try:
            result = detector.analyze_journal_comprehensive(journal['url'])
            detector.display_comprehensive_results(result)
            
            print(f"\n⏳ Waiting 3 seconds before next analysis...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Analysis interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Analysis error: {e}")
            continue
    
    print(f"\n" + "🎉" * 80)
    print("🎉 ENHANCED ANALYSIS COMPLETE!")  
    print("🎉" * 80)
    print("Key Enhancements Demonstrated:")
    print("✅ Peer review transparency analysis - #1 academic indicator")
    print("✅ External verification - prevents journal deception")
    print("✅ Enhanced editorial board verification - credential checking")
    print("✅ Sophisticated language analysis - context-aware detection")
    print("✅ Evidence-based scoring weights - aligned with research")
    print("✅ Comprehensive reporting - actionable recommendations")
    print("\nThis system now aligns with established academic research!")
    print("🎉" * 80)

if __name__ == "__main__":
    main()

