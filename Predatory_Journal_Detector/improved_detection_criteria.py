#!/usr/bin/env python3
"""
Improved Predatory Journal Detection Criteria
Based on comprehensive academic research and established guidelines

This module implements evidence-based criteria from:
- Committee on Publication Ethics (COPE)
- Think-Check-Submit Initiative
- Eriksson & Helgesson validated criteria
- Jeffrey Beall's research
- Recent academic literature (2023-2024)
"""

import re
import requests
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Structured result from predatory journal detection"""
    overall_score: float
    risk_level: str
    confidence: float
    critical_flags: List[str]
    warnings: List[str]
    detailed_scores: Dict[str, float]
    recommendations: List[str]

class ImprovedPredatoryDetector:
    """
    Enhanced predatory journal detector based on academic research
    
    Implements evidence-based criteria with proper weighting according to
    established academic guidelines and recent research findings.
    """
    
    # Evidence-based scoring weights (total = 100)
    SCORING_WEIGHTS = {
        'peer_review_analysis': 30,      # CRITICAL - Primary indicator per all sources
        'predatory_language': 25,        # HIGH - Well-validated in literature  
        'editorial_board_verification': 20, # HIGH - Core academic practice
        'indexing_verification': 15,     # MODERATE - Important for credibility
        'contact_transparency': 10       # LOW - Less critical than originally thought
    }
    
    def __init__(self):
        """Initialize improved detection system"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Journal Analyzer/1.0 (Research Integrity Tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Load known legitimate databases for verification
        self.legitimate_databases = {
            'major': ['pubmed', 'scopus', 'web of science', 'doaj'],
            'field_specific': ['ieee xplore', 'acm digital library', 'jstor', 'wiley online'],
            'regional': ['scielo', 'redalyc', 'african journals online']
        }
        
        # Load sophisticated predatory language patterns
        self.predatory_patterns = self._load_predatory_patterns()
        
    def _load_predatory_patterns(self) -> Dict[str, List[str]]:
        """Load evidence-based predatory language patterns"""
        return {
            'critical_red_flags': [
                # Guaranteed acceptance patterns (CRITICAL)
                r'guaranteed?\s+(?:acceptance|publication)',
                r'we\s+accept\s+all\s+(?:papers?|manuscripts?|submissions?)',
                r'(?:100%|assured|certain)\s+acceptance',
                
                # Fake review process (CRITICAL) 
                r'no\s+(?:peer\s+)?review\s+(?:required|needed)',
                r'minimal\s+(?:peer\s+)?review',
                r'(?:skip|bypass)\s+(?:peer\s+)?review',
                
                # Payment manipulation (CRITICAL)
                r'pay\s+(?:only\s+)?after\s+(?:acceptance|publication)',
                r'no\s+(?:fees?|charges?)\s+(?:until|before)\s+acceptance',
                r'bitcoin|cryptocurrency\s+payment',
                
                # Fake metrics (CRITICAL)
                r'impact\s+factor\s+(?:will\s+be|guaranteed|assured)\s+\d+',
                r'fake\s+impact\s+factor',
                r'(?:increase|boost|improve)\s+your\s+(?:h-index|citations?)',
            ],
            
            'high_risk_indicators': [
                # Unrealistic timelines (HIGH RISK)
                r'(?:publish|review|accept)\s+(?:within|in)\s+(?:\d+\s+)?(?:hours?|24\s+hours?)',
                r'(?:immediate|instant|same[- ]day)\s+(?:publication|review|acceptance)',
                r'rapid\s+publication\s+within\s+\d+\s+days?',
                
                # Aggressive marketing (HIGH RISK)
                r'limited\s+time\s+offer',
                r'special\s+(?:discount|promotion|price)',
                r'act\s+(?:now|quickly|fast)',
                
                # False authority claims (HIGH RISK)
                r'(?:ranked|top)\s+\#?\d+\s+(?:journal|publisher)',
                r'world[- ](?:class|renowned|famous)\s+(?:journal|publisher)',
                r'international\s+(?:prestige|recognition|acclaim)',
            ],
            
            'moderate_risk_indicators': [
                # Speed emphasis (MODERATE)
                r'fast\s+track\s+(?:publication|review)',
                r'quick\s+(?:publication|review|turnaround)',
                r'speedy\s+(?:publication|review|process)',
                
                # Promotional language (MODERATE)
                r'(?:excellent|outstanding|prestigious)\s+opportunity',
                r'(?:enhance|boost|improve)\s+your\s+(?:career|reputation)',
                r'join\s+(?:thousands|millions)\s+of\s+(?:authors|researchers)',
            ]
        }
    
    def analyze_journal(self, url: str, content: str = None) -> DetectionResult:
        """
        Comprehensive analysis using evidence-based criteria
        
        Args:
            url: Journal website URL
            content: Optional pre-fetched content
            
        Returns:
            DetectionResult with detailed scoring and recommendations
        """
        logger.info(f"Starting comprehensive analysis of {url}")
        
        if content is None:
            content = self._fetch_content(url)
            
        if not content:
            return DetectionResult(
                overall_score=100.0,
                risk_level="Unable to analyze",
                confidence=0.0,
                critical_flags=["Could not access website"],
                warnings=[],
                detailed_scores={},
                recommendations=["Verify website accessibility"]
            )
        
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True).lower()
        
        # Perform evidence-based analysis
        results = {}
        results['peer_review'] = self._analyze_peer_review_process(text, soup)
        results['predatory_language'] = self._analyze_predatory_language(text)
        results['editorial_board'] = self._analyze_editorial_board(text, soup)
        results['indexing'] = self._analyze_indexing_claims(text)
        results['contact'] = self._analyze_contact_transparency(text, soup)
        
        return self._calculate_final_score(results, url)
    
    def _analyze_peer_review_process(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        Analyze peer review process transparency (30 points - CRITICAL)
        
        Based on COPE guidelines and academic standards:
        - Clear description of review process
        - Reasonable timelines  
        - Reviewer qualifications mentioned
        - Review stages described
        """
        logger.debug("Analyzing peer review process transparency")
        
        score = 0
        flags = []
        details = {}
        
        # Look for peer review mentions
        review_keywords = [
            'peer review', 'review process', 'editorial process',
            'manuscript review', 'reviewer', 'review criteria'
        ]
        
        review_mentions = sum(1 for keyword in review_keywords if keyword in text)
        details['review_mentions'] = review_mentions
        
        if review_mentions == 0:
            score += 25  # CRITICAL: No mention of peer review
            flags.append("No peer review process described")
        elif review_mentions < 3:
            score += 15  # HIGH: Minimal mention
            flags.append("Limited peer review information")
        
        # Check for process clarity
        clarity_indicators = [
            'review stages', 'review criteria', 'reviewer guidelines',
            'editorial decision', 'revision process', 'acceptance criteria'
        ]
        
        clarity_score = sum(1 for indicator in clarity_indicators if indicator in text)
        details['process_clarity'] = clarity_score
        
        if clarity_score == 0:
            score += 20  # No clear process description
            flags.append("Unclear review process")
        elif clarity_score < 2:
            score += 10  # Limited clarity
        
        # Check for unrealistic timeline promises
        fast_patterns = [
            r'(?:review|decision)\s+(?:within|in)\s+(?:\d+\s+)?(?:hours?|days?)',
            r'(?:immediate|instant|rapid)\s+(?:review|decision)',
            r'(?:24\s+hours?|same\s+day)\s+(?:review|turnaround)'
        ]
        
        for pattern in fast_patterns:
            if re.search(pattern, text):
                score += 15  # Unrealistic timelines
                flags.append("Unrealistic review timeline promises")
                break
        
        # Check for reviewer qualification mentions
        qualification_keywords = [
            'qualified reviewer', 'expert reviewer', 'reviewer expertise',
            'reviewer credentials', 'reviewer selection'
        ]
        
        has_qualifications = any(keyword in text for keyword in qualification_keywords)
        details['mentions_reviewer_qualifications'] = has_qualifications
        
        if not has_qualifications:
            score += 10  # No mention of reviewer qualifications
        
        return {
            'score': min(score, 30),  # Cap at maximum weight
            'flags': flags,
            'details': details
        }
    
    def _analyze_predatory_language(self, text: str) -> Dict:
        """
        Analyze for predatory language patterns (25 points - HIGH)
        
        Based on validated patterns from academic literature:
        - Critical red flags (immediate high risk)
        - High-risk indicators 
        - Moderate-risk indicators
        """
        logger.debug("Analyzing predatory language patterns")
        
        score = 0
        flags = []
        found_patterns = {'critical': [], 'high_risk': [], 'moderate_risk': []}
        
        # Critical red flags (25 points each, max 25 total)
        for pattern in self.predatory_patterns['critical_red_flags']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_patterns['critical'].extend(matches)
                score = 25  # Any critical flag = maximum score
                flags.append(f"Critical predatory indicator: {matches[0]}")
                break  # One critical flag is enough
        
        # If no critical flags, check high-risk indicators
        if score == 0:
            for pattern in self.predatory_patterns['high_risk_indicators']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    found_patterns['high_risk'].extend(matches)
                    score += 8  # 8 points per high-risk indicator
                    flags.append(f"High-risk indicator: {matches[0]}")
        
        # Moderate-risk indicators (additional points)
        moderate_count = 0
        for pattern in self.predatory_patterns['moderate_risk_indicators']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_patterns['moderate_risk'].extend(matches)
                moderate_count += len(matches)
        
        if moderate_count > 0:
            score += min(moderate_count * 3, 10)  # 3 points each, max 10
            flags.append(f"Moderate-risk indicators: {moderate_count} found")
        
        return {
            'score': min(score, 25),  # Cap at maximum weight
            'flags': flags,
            'details': {
                'critical_patterns': found_patterns['critical'],
                'high_risk_patterns': found_patterns['high_risk'], 
                'moderate_risk_patterns': found_patterns['moderate_risk']
            }
        }
    
    def _analyze_editorial_board(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        Analyze editorial board credibility (20 points - HIGH)
        
        Based on academic standards:
        - Presence of editorial board information
        - Editor credentials and affiliations
        - Relevant expertise indicators
        """
        logger.debug("Analyzing editorial board credibility")
        
        score = 0
        flags = []
        details = {}
        
        # Look for editorial board sections
        board_keywords = [
            'editorial board', 'editors', 'editorial team', 'associate editors',
            'editor-in-chief', 'managing editor', 'editorial committee'
        ]
        
        board_mentions = sum(1 for keyword in board_keywords if keyword in text)
        details['board_mentions'] = board_mentions
        
        if board_mentions == 0:
            score += 15  # No editorial board information
            flags.append("No editorial board information found")
        elif board_mentions < 2:
            score += 8   # Limited editorial information
            flags.append("Limited editorial board information")
        
        # Look for credential indicators
        credential_patterns = [
            r'(?:dr\.?|prof\.?|professor)\s+\w+',  # Academic titles
            r'ph\.?d\.?|phd',                      # PhD mentions  
            r'university|college|institute',       # Institutional affiliations
            r'research|department|faculty'         # Academic contexts
        ]
        
        credential_matches = 0
        for pattern in credential_patterns:
            credential_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        details['credential_indicators'] = credential_matches
        
        if credential_matches == 0:
            score += 10  # No academic credentials mentioned
            flags.append("No editor credentials or affiliations found")
        elif credential_matches < 5:
            score += 5   # Few credential mentions
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'same\s+editorial\s+board',           # Same board across journals
            r'no\s+editorial\s+board',             # Explicitly no board
            r'editors?\s+(?:anonymous|confidential)' # Anonymous editors
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 10
                flags.append("Suspicious editorial board patterns detected")
                break
        
        return {
            'score': min(score, 20),  # Cap at maximum weight
            'flags': flags,
            'details': details
        }
    
    def _analyze_indexing_claims(self, text: str) -> Dict:
        """
        Analyze indexing and impact factor claims (15 points - MODERATE)
        
        Based on common predatory tactics:
        - False database indexing claims
        - Fake impact factor metrics
        - Suspicious indexing language
        """
        logger.debug("Analyzing indexing and impact factor claims")
        
        score = 0
        flags = []
        details = {}
        
        # Check for indexing claims
        indexing_keywords = [
            'indexed', 'indexing', 'database', 'pubmed', 'scopus', 
            'web of science', 'doaj', 'impact factor'
        ]
        
        indexing_mentions = sum(1 for keyword in indexing_keywords if keyword in text)
        details['indexing_mentions'] = indexing_mentions
        
        # Look for suspicious indexing claims
        suspicious_indexing = [
            r'indexed\s+in\s+(?:all\s+)?(?:major\s+)?databases?',
            r'high\s+impact\s+factor\s+(?:guaranteed|assured)',
            r'impact\s+factor\s+(?:will\s+be|of)\s+\d+',
            r'indexed\s+in\s+\d+\s+databases?'
        ]
        
        for pattern in suspicious_indexing:
            if re.search(pattern, text, re.IGNORECASE):
                score += 8
                flags.append("Suspicious indexing claims detected")
                details['suspicious_indexing'] = True
                break
        
        # Look for fake impact factor patterns
        fake_if_patterns = [
            r'impact\s+factor[:\s]+\d+\.\d+',  # Specific IF claims
            r'if[:\s]+\d+\.\d+',               # IF abbreviation
            r'journal\s+impact\s+factor[:\s]+\d+' # JIF claims
        ]
        
        for pattern in fake_if_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += 5
                flags.append(f"Impact factor claims found: {len(matches)}")
                details['impact_factor_claims'] = matches
                break
        
        # Check for complete absence of indexing info
        if indexing_mentions == 0:
            score += 3  # Slight penalty for no indexing information
            details['no_indexing_info'] = True
        
        return {
            'score': min(score, 15),  # Cap at maximum weight  
            'flags': flags,
            'details': details
        }
    
    def _analyze_contact_transparency(self, text: str, soup: BeautifulSoup) -> Dict:
        """
        Analyze contact information transparency (10 points - LOW priority)
        
        Note: Reduced weight based on academic research showing this is
        less critical than originally thought.
        """
        logger.debug("Analyzing contact transparency")
        
        score = 0
        flags = []
        details = {}
        
        # Find contact information
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phones = re.findall(r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
        
        details['emails_found'] = len(emails)
        details['phones_found'] = len(phones)
        
        # Basic contact scoring
        if len(emails) == 0:
            score += 6  # No email contact
            flags.append("No email contact information")
        elif len(emails) == 1:
            score += 3  # Limited email contact
        
        if len(phones) == 0:
            score += 4  # No phone contact
        
        # Check for unprofessional email domains
        unprofessional_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        for email in emails:
            domain = email.split('@')[1].lower()
            if domain in unprofessional_domains:
                score += 3
                flags.append("Unprofessional email domains detected")
                break
        
        return {
            'score': min(score, 10),  # Cap at maximum weight
            'flags': flags,
            'details': details
        }
    
    def _calculate_final_score(self, results: Dict, url: str) -> DetectionResult:
        """Calculate final risk score and generate comprehensive report"""
        
        # Calculate weighted score
        total_score = 0
        detailed_scores = {}
        all_flags = []
        all_warnings = []
        
        for category, weight in self.SCORING_WEIGHTS.items():
            if category == 'peer_review_analysis':
                cat_result = results['peer_review']
            elif category == 'predatory_language':
                cat_result = results['predatory_language']  
            elif category == 'editorial_board_verification':
                cat_result = results['editorial_board']
            elif category == 'indexing_verification':
                cat_result = results['indexing']
            elif category == 'contact_transparency':
                cat_result = results['contact']
            
            cat_score = cat_result['score']
            detailed_scores[category] = cat_score
            total_score += cat_score
            
            # Collect flags
            if cat_result['flags']:
                if cat_score >= weight * 0.7:  # High score in category
                    all_flags.extend(cat_result['flags'])
                else:
                    all_warnings.extend(cat_result['flags'])
        
        # Determine risk level and confidence
        if total_score >= 80:
            risk_level = "Very High Risk"
            confidence = 0.95
        elif total_score >= 60:
            risk_level = "High Risk" 
            confidence = 0.85
        elif total_score >= 40:
            risk_level = "Moderate Risk"
            confidence = 0.75
        elif total_score >= 20:
            risk_level = "Low Risk"
            confidence = 0.65
        else:
            risk_level = "Very Low Risk"
            confidence = 0.55
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, total_score)
        
        return DetectionResult(
            overall_score=total_score,
            risk_level=risk_level,
            confidence=confidence,
            critical_flags=all_flags,
            warnings=all_warnings,
            detailed_scores=detailed_scores,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: Dict, total_score: float) -> List[str]:
        """Generate evidence-based recommendations"""
        
        recommendations = []
        
        if total_score >= 70:
            recommendations.append("⚠️ AVOID: Multiple serious red flags detected")
            recommendations.append("Consider reporting to institutional library")
            
        if results['peer_review']['score'] >= 20:
            recommendations.append("❌ Inadequate peer review process description")
            
        if results['predatory_language']['flags']:
            recommendations.append("🚨 Predatory language patterns detected")
            
        if results['editorial_board']['score'] >= 15:
            recommendations.append("👥 Editorial board credibility concerns")
            
        if total_score <= 30:
            recommendations.append("✅ Appears to follow academic standards")
            recommendations.append("Consider additional verification if uncertain")
            
        recommendations.append("💡 Use Think-Check-Submit checklist for final verification")
        
        return recommendations
    
    def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch website content with proper error handling"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    detector = ImprovedPredatoryDetector()
    
    # Test with a legitimate journal
    result = detector.analyze_journal("https://journals.plos.org/plosone/")
    print(f"Score: {result.overall_score}/100")
    print(f"Risk: {result.risk_level}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Flags: {result.critical_flags}")
    print(f"Recommendations: {result.recommendations}")

