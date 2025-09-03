#!/usr/bin/env python3
"""
Comprehensive Scoring System for Predatory Journal Assessment
Multi-dimensional scoring with detailed explanations
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

class PredatoryScoringSystem:
    """
    Comprehensive scoring system that combines multiple assessment dimensions
    to produce interpretable predatory risk scores
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Scoring weights for different dimensions
        self.dimension_weights = {
            'website_quality': 0.15,
            'editorial_board': 0.20,
            'submission_process': 0.15,
            'contact_information': 0.10,
            'publication_fees': 0.15,
            'content_quality': 0.10,
            'domain_analysis': 0.10,
            'bibliometric': 0.05
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            'very_low': 20,
            'low': 40,
            'moderate': 60,
            'high': 80,
            'very_high': 100
        }
        
        # Critical indicators that automatically increase risk
        self.critical_indicators = [
            'guaranteed_acceptance',
            'fake_impact_factor',
            'bitcoin_payment',
            'within_24_hours',
            'no_peer_review'
        ]
    
    def calculate_comprehensive_score(self, scraped_data: Dict, ml_prediction: Dict = None) -> Dict:
        """
        Calculate comprehensive predatory risk score
        
        Args:
            scraped_data: Dictionary containing scraped journal data
            ml_prediction: Optional ML model prediction results
            
        Returns:
            Dictionary containing detailed scoring results
        """
        scoring_start = datetime.now()
        
        result = {
            'journal_url': scraped_data.get('url', ''),
            'analysis_timestamp': scoring_start.isoformat(),
            'dimension_scores': {},
            'warning_flags': [],
            'positive_indicators': [],
            'critical_issues': [],
            'overall_score': 0,
            'risk_level': 'Unknown',
            'confidence': 0,
            'recommendation': '',
            'detailed_analysis': {}
        }
        
        try:
            # Calculate scores for each dimension
            result['dimension_scores']['website_quality'] = self._score_website_quality(scraped_data)
            result['dimension_scores']['editorial_board'] = self._score_editorial_board(scraped_data)
            result['dimension_scores']['submission_process'] = self._score_submission_process(scraped_data)
            result['dimension_scores']['contact_information'] = self._score_contact_information(scraped_data)
            result['dimension_scores']['publication_fees'] = self._score_publication_fees(scraped_data)
            result['dimension_scores']['content_quality'] = self._score_content_quality(scraped_data)
            result['dimension_scores']['domain_analysis'] = self._score_domain_analysis(scraped_data)
            result['dimension_scores']['bibliometric'] = self._score_bibliometric(scraped_data)
            
            # Calculate weighted overall score
            overall_score = sum(
                score['score'] * self.dimension_weights[dimension]
                for dimension, score in result['dimension_scores'].items()
            )
            
            # Collect warning flags and positive indicators
            for dimension_data in result['dimension_scores'].values():
                result['warning_flags'].extend(dimension_data.get('warnings', []))
                result['positive_indicators'].extend(dimension_data.get('positives', []))
                result['critical_issues'].extend(dimension_data.get('critical', []))
            
            # Apply critical issue penalties
            critical_penalty = len(result['critical_issues']) * 15
            overall_score = min(overall_score + critical_penalty, 100)
            
            # Incorporate ML prediction if available
            if ml_prediction and 'predatory_score' in ml_prediction:
                ml_score = ml_prediction['predatory_score']
                # Weight combination: 70% rule-based, 30% ML
                overall_score = 0.7 * overall_score + 0.3 * ml_score
            
            result['overall_score'] = round(overall_score, 2)
            
            # Determine risk level and confidence
            risk_level, confidence = self._determine_risk_level(overall_score, result)
            result['risk_level'] = risk_level
            result['confidence'] = confidence
            
            # Generate recommendation
            result['recommendation'] = self._generate_recommendation(result)
            
            # Create detailed analysis
            result['detailed_analysis'] = self._create_detailed_analysis(result, scraped_data)
            
        except Exception as e:
            self.logger.error(f"Scoring failed: {e}")
            result['error'] = str(e)
            result['overall_score'] = 50  # Neutral score for errors
            result['risk_level'] = 'Unknown'
            result['recommendation'] = 'Manual review required due to scoring error'
        
        return result
    
    def _score_website_quality(self, data: Dict) -> Dict:
        """Score website quality and professionalism"""
        quality_metrics = data.get('quality_metrics', {})
        
        base_score = quality_metrics.get('overall_score', 0)
        warnings = []
        positives = []
        critical = []
        
        # Technical quality checks
        if not data.get('has_ssl', False):
            warnings.append("No SSL certificate - security risk")
            base_score += 15
        else:
            positives.append("Has SSL certificate")
        
        # Response time
        response_time = data.get('response_time', 0)
        if response_time > 5:
            warnings.append("Very slow website response time")
            base_score += 10
        elif response_time < 2:
            positives.append("Fast website response time")
        
        # Website issues
        issues = quality_metrics.get('issues', [])
        if 'Not mobile responsive' in issues:
            warnings.append("Website not mobile responsive")
            base_score += 10
        
        # Design quality
        design_score = quality_metrics.get('design_score', 0)
        if design_score < 30:
            warnings.append("Poor website design quality")
            base_score += 15
        elif design_score > 70:
            positives.append("Professional website design")
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'technical_score': quality_metrics.get('technical_score', 0),
                'design_score': design_score,
                'content_score': quality_metrics.get('content_score', 0),
                'response_time': response_time,
                'ssl_enabled': data.get('has_ssl', False)
            }
        }
    
    def _score_editorial_board(self, data: Dict) -> Dict:
        """Score editorial board quality and legitimacy"""
        editorial_info = data.get('editorial_board', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        board_size = editorial_info.get('board_size', 0)
        
        # Board size assessment
        if board_size == 0:
            critical.append("No editorial board information found")
            base_score += 40
        elif board_size < 5:
            warnings.append("Very small editorial board")
            base_score += 20
        elif board_size < 10:
            warnings.append("Small editorial board")
            base_score += 10
        elif board_size >= 15:
            positives.append("Adequate editorial board size")
        
        # Editor-in-Chief
        if not editorial_info.get('editor_in_chief'):
            warnings.append("No Editor-in-Chief identified")
            base_score += 15
        else:
            positives.append("Has identified Editor-in-Chief")
        
        # Board quality score
        quality_score = editorial_info.get('quality_score', 0)
        if quality_score < 30:
            warnings.append("Poor editorial board information quality")
            base_score += 20
        elif quality_score > 70:
            positives.append("High-quality editorial board information")
        
        # Member completeness (if we have members data)
        members = editorial_info.get('members', [])
        if members:
            complete_members = sum(1 for member in members 
                                 if member.get('name') and member.get('affiliation'))
            completeness_ratio = complete_members / len(members) if members else 0
            
            if completeness_ratio < 0.3:
                warnings.append("Incomplete editorial board member information")
                base_score += 15
            elif completeness_ratio > 0.8:
                positives.append("Complete editorial board member information")
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'board_size': board_size,
                'has_editor_in_chief': bool(editorial_info.get('editor_in_chief')),
                'quality_score': quality_score,
                'member_count': len(members)
            }
        }
    
    def _score_submission_process(self, data: Dict) -> Dict:
        """Score submission process transparency and legitimacy"""
        submission_info = data.get('submission_info', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        # Guidelines availability
        if not submission_info.get('has_guidelines', False):
            warnings.append("No submission guidelines found")
            base_score += 20
        else:
            positives.append("Has submission guidelines")
        
        # Peer review mention
        if not submission_info.get('peer_review_mentioned', False):
            warnings.append("No mention of peer review process")
            base_score += 25
        else:
            positives.append("Peer review process mentioned")
        
        # Timeline analysis
        review_timeline = submission_info.get('review_timeline')
        if review_timeline:
            try:
                days = int(review_timeline)
                if days < 7:
                    critical.append("Unrealistically fast review timeline")
                    base_score += 30
                elif days < 14:
                    warnings.append("Very fast review timeline")
                    base_score += 15
                elif 30 <= days <= 90:
                    positives.append("Reasonable review timeline")
            except:
                pass
        
        # Quality score
        quality_score = submission_info.get('quality_score', 0)
        if quality_score < 30:
            warnings.append("Poor submission process information")
            base_score += 15
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'has_guidelines': submission_info.get('has_guidelines', False),
                'peer_review_mentioned': submission_info.get('peer_review_mentioned', False),
                'timeline_mentioned': submission_info.get('timeline_mentioned', False),
                'review_timeline': review_timeline
            }
        }
    
    def _score_contact_information(self, data: Dict) -> Dict:
        """Score contact information completeness and legitimacy"""
        contact_info = data.get('contact_info', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        # Contact method availability
        contact_methods = 0
        if contact_info.get('has_email', False):
            contact_methods += 1
            positives.append("Has email contact")
        else:
            warnings.append("No email contact found")
            base_score += 15
        
        if contact_info.get('has_phone', False):
            contact_methods += 1
            positives.append("Has phone contact")
        
        if contact_info.get('has_address', False):
            contact_methods += 1
            positives.append("Has physical address")
        else:
            warnings.append("No physical address provided")
            base_score += 10
        
        if contact_methods == 0:
            critical.append("No contact information found")
            base_score += 30
        elif contact_methods == 1:
            warnings.append("Limited contact methods available")
            base_score += 10
        
        # Quality assessment
        quality_score = contact_info.get('quality_score', 0)
        if quality_score < 40:
            warnings.append("Poor contact information quality")
            base_score += 10
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'contact_methods': contact_methods,
                'has_email': contact_info.get('has_email', False),
                'has_phone': contact_info.get('has_phone', False),
                'has_address': contact_info.get('has_address', False),
                'email_count': len(contact_info.get('emails', [])),
                'quality_score': quality_score
            }
        }
    
    def _score_publication_fees(self, data: Dict) -> Dict:
        """Score publication fees reasonableness and payment methods"""
        fees_info = data.get('fees_info', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        # Fee analysis
        if fees_info.get('has_fees', False):
            fees_amount = fees_info.get('fees_amount')
            if fees_amount:
                try:
                    amount = float(str(fees_amount).replace(',', ''))
                    
                    if amount > 3000:
                        critical.append("Extremely high publication fees")
                        base_score += 25
                    elif amount > 2000:
                        warnings.append("Very high publication fees")
                        base_score += 15
                    elif amount > 1500:
                        warnings.append("High publication fees")
                        base_score += 10
                    elif 500 <= amount <= 1500:
                        positives.append("Reasonable publication fees")
                    elif amount < 100:
                        warnings.append("Unusually low publication fees")
                        base_score += 10
                except:
                    warnings.append("Unclear fee information")
                    base_score += 5
        
        # Suspicious payment methods
        if fees_info.get('suspicious_payment', False):
            critical.append("Suspicious payment methods detected")
            base_score += 30
        
        # Fee transparency
        quality_score = fees_info.get('quality_score', 0)
        if quality_score < 0:  # Negative indicates problems
            warnings.append("Issues with fee information")
            base_score += abs(quality_score) // 10
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'has_fees': fees_info.get('has_fees', False),
                'fees_amount': fees_info.get('fees_amount'),
                'currency': fees_info.get('currency'),
                'suspicious_payment': fees_info.get('suspicious_payment', False)
            }
        }
    
    def _score_content_quality(self, data: Dict) -> Dict:
        """Score website content quality and language"""
        content_quality = data.get('content_quality', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        # Overall content quality
        overall_score = content_quality.get('overall_score', 0)
        if overall_score < 30:
            warnings.append("Poor content quality")
            base_score += 20
        elif overall_score > 70:
            positives.append("Good content quality")
        
        # Language analysis
        language_analysis = content_quality.get('language_analysis', {})
        if not language_analysis.get('is_english', False):
            warnings.append("Content not in English")
            base_score += 5
        
        # Grammar and spelling
        grammar_errors = language_analysis.get('estimated_spelling_errors', 0)
        basic_metrics = content_quality.get('basic_metrics', {})
        word_count = basic_metrics.get('word_count', 1)
        
        if word_count > 0:
            error_rate = grammar_errors / word_count
            if error_rate > 0.05:
                warnings.append("High grammar/spelling error rate")
                base_score += 15
            elif error_rate > 0.02:
                warnings.append("Moderate grammar/spelling errors")
                base_score += 10
        
        # Content length
        if word_count < 200:
            warnings.append("Very little content on website")
            base_score += 10
        elif word_count > 1000:
            positives.append("Comprehensive website content")
        
        # Predatory indicators
        predatory_indicators = content_quality.get('predatory_indicators', {})
        high_risk_count = len(predatory_indicators.get('high_risk', []))
        medium_risk_count = len(predatory_indicators.get('medium_risk', []))
        
        if high_risk_count > 0:
            critical.append(f"High-risk predatory indicators found: {high_risk_count}")
            base_score += high_risk_count * 20
        
        if medium_risk_count > 0:
            warnings.append(f"Medium-risk predatory indicators found: {medium_risk_count}")
            base_score += medium_risk_count * 10
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'overall_score': overall_score,
                'word_count': word_count,
                'is_english': language_analysis.get('is_english', False),
                'grammar_errors': grammar_errors,
                'predatory_risk_score': predatory_indicators.get('risk_score', 0)
            }
        }
    
    def _score_domain_analysis(self, data: Dict) -> Dict:
        """Score domain legitimacy and technical characteristics"""
        technical_analysis = data.get('technical_analysis', {})
        domain_info = technical_analysis.get('domain_info', {})
        
        base_score = domain_info.get('risk_score', 50)  # Use domain risk score directly
        warnings = []
        positives = []
        critical = []
        
        # Domain age
        whois_info = domain_info.get('whois_info', {})
        domain_age = whois_info.get('domain_age_days', 0)
        
        if domain_age < 30:
            critical.append("Very new domain (less than 1 month)")
        elif domain_age < 365:
            warnings.append("New domain (less than 1 year)")
        elif domain_age > 365 * 3:
            positives.append("Established domain (over 3 years)")
        
        # Legitimate publisher check
        if domain_info.get('legitimate_publisher', False):
            positives.append("Known legitimate publisher")
            base_score = max(0, base_score - 30)  # Reduce risk for known publishers
        
        # Academic domain
        if domain_info.get('academic_domain', False):
            positives.append("Academic domain")
            base_score = max(0, base_score - 20)
        
        # Suspicious indicators
        if domain_info.get('suspicious_tld', False):
            warnings.append("Suspicious top-level domain")
        
        if domain_info.get('typosquatting_risk', False):
            critical.append("Possible typosquatting of legitimate publisher")
        
        # SSL analysis
        ssl_info = domain_info.get('ssl_info', {})
        if not ssl_info.get('has_ssl', False):
            warnings.append("No SSL certificate")
        elif ssl_info.get('self_signed', False):
            warnings.append("Self-signed SSL certificate")
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'domain_age_days': domain_age,
                'legitimate_publisher': domain_info.get('legitimate_publisher', False),
                'academic_domain': domain_info.get('academic_domain', False),
                'suspicious_tld': domain_info.get('suspicious_tld', False),
                'has_ssl': ssl_info.get('has_ssl', False)
            }
        }
    
    def _score_bibliometric(self, data: Dict) -> Dict:
        """Score bibliometric claims and legitimacy"""
        metadata = data.get('metadata', {})
        
        base_score = 0
        warnings = []
        positives = []
        critical = []
        
        # Impact factor claims
        claimed_if = metadata.get('claimed_impact_factor')
        if claimed_if:
            try:
                if_value = float(claimed_if)
                if if_value > 20:
                    critical.append("Extremely high impact factor claim")
                    base_score += 30
                elif if_value > 10:
                    warnings.append("Very high impact factor claim")
                    base_score += 15
                elif if_value > 5:
                    warnings.append("High impact factor claim - verify independently")
                    base_score += 5
                elif if_value > 0:
                    positives.append("Reasonable impact factor claim")
            except:
                warnings.append("Invalid impact factor format")
                base_score += 10
        
        # ISSN presence
        issns = metadata.get('issns', [])
        if not issns:
            warnings.append("No ISSN found")
            base_score += 15
        elif len(issns) > 2:
            warnings.append("Unusually many ISSNs")
            base_score += 5
        else:
            positives.append("Has ISSN")
        
        # Publisher information
        publisher = metadata.get('publisher', '')
        if not publisher:
            warnings.append("No publisher information")
            base_score += 10
        else:
            # Check against known legitimate publishers (simplified)
            known_publishers = ['elsevier', 'springer', 'wiley', 'nature', 'taylor', 'sage']
            if any(pub in publisher.lower() for pub in known_publishers):
                positives.append("Known legitimate publisher")
                base_score = max(0, base_score - 20)
        
        return {
            'score': min(base_score, 100),
            'warnings': warnings,
            'positives': positives,
            'critical': critical,
            'details': {
                'claimed_impact_factor': claimed_if,
                'issn_count': len(issns),
                'has_publisher': bool(publisher),
                'publisher': publisher
            }
        }
    
    def _determine_risk_level(self, overall_score: float, result: Dict) -> Tuple[str, float]:
        """Determine risk level and confidence based on score and indicators"""
        
        # Base risk level determination
        if overall_score >= self.risk_thresholds['very_high']:
            risk_level = "Very High Risk"
            base_confidence = 0.9
        elif overall_score >= self.risk_thresholds['high']:
            risk_level = "High Risk"
            base_confidence = 0.8
        elif overall_score >= self.risk_thresholds['moderate']:
            risk_level = "Moderate Risk"
            base_confidence = 0.7
        elif overall_score >= self.risk_thresholds['low']:
            risk_level = "Low Risk"
            base_confidence = 0.6
        else:
            risk_level = "Very Low Risk"
            base_confidence = 0.8
        
        # Adjust confidence based on critical issues and positive indicators
        confidence_adjustment = 0
        
        # Critical issues increase confidence in high risk assessment
        critical_count = len(result.get('critical_issues', []))
        if critical_count > 0 and overall_score > 50:
            confidence_adjustment += min(critical_count * 0.1, 0.2)
        
        # Many positive indicators increase confidence in low risk assessment
        positive_count = len(result.get('positive_indicators', []))
        if positive_count > 5 and overall_score < 50:
            confidence_adjustment += min((positive_count - 5) * 0.05, 0.15)
        
        # Many warning flags in moderate range reduce confidence
        warning_count = len(result.get('warning_flags', []))
        if warning_count > 10:
            confidence_adjustment -= min((warning_count - 10) * 0.02, 0.1)
        
        final_confidence = max(0.5, min(1.0, base_confidence + confidence_adjustment))
        
        return risk_level, round(final_confidence * 100, 1)
    
    def _generate_recommendation(self, result: Dict) -> str:
        """Generate human-readable recommendation based on analysis"""
        overall_score = result['overall_score']
        risk_level = result['risk_level']
        critical_count = len(result.get('critical_issues', []))
        warning_count = len(result.get('warning_flags', []))
        
        if critical_count > 2:
            return "AVOID: Multiple critical predatory indicators detected. This journal shows clear signs of predatory behavior."
        elif risk_level == "Very High Risk":
            return "AVOID: Very high risk of predatory behavior. Seek alternative legitimate journals."
        elif risk_level == "High Risk":
            return "CAUTION: High risk detected. Investigate thoroughly before considering submission."
        elif risk_level == "Moderate Risk":
            if warning_count > 5:
                return "INVESTIGATE: Multiple concerns identified. Thorough verification recommended."
            else:
                return "CAUTION: Some risk indicators present. Independent verification advised."
        elif risk_level == "Low Risk":
            return "PROCEED WITH CAUTION: Appears mostly legitimate but verify independently."
        else:
            return "LOW RISK: Appears to be a legitimate journal based on available indicators."
    
    def _create_detailed_analysis(self, result: Dict, scraped_data: Dict) -> Dict:
        """Create detailed analysis summary"""
        analysis = {
            'summary': {
                'total_warnings': len(result.get('warning_flags', [])),
                'total_positives': len(result.get('positive_indicators', [])),
                'critical_issues': len(result.get('critical_issues', [])),
                'dimensions_analyzed': len(result['dimension_scores']),
                'worst_dimension': None,
                'best_dimension': None
            },
            'dimension_breakdown': {},
            'key_concerns': result.get('critical_issues', [])[:5],  # Top 5 critical issues
            'positive_aspects': result.get('positive_indicators', [])[:5],  # Top 5 positives
            'improvement_suggestions': []
        }
        
        # Find best and worst scoring dimensions
        dimension_scores = {k: v['score'] for k, v in result['dimension_scores'].items()}
        if dimension_scores:
            analysis['summary']['worst_dimension'] = max(dimension_scores, key=dimension_scores.get)
            analysis['summary']['best_dimension'] = min(dimension_scores, key=dimension_scores.get)
        
        # Create dimension breakdown
        for dimension, data in result['dimension_scores'].items():
            analysis['dimension_breakdown'][dimension] = {
                'score': data['score'],
                'risk_level': 'High' if data['score'] > 60 else 'Moderate' if data['score'] > 30 else 'Low',
                'warning_count': len(data.get('warnings', [])),
                'positive_count': len(data.get('positives', [])),
                'key_issues': data.get('warnings', [])[:3]
            }
        
        # Generate improvement suggestions
        if result['overall_score'] > 50:
            analysis['improvement_suggestions'] = [
                "Consider alternative journals with better track records",
                "Verify all claims independently through official databases",
                "Check journal inclusion in PubMed, Scopus, or Web of Science",
                "Consult institutional library or colleagues for advice",
                "Review recent publications and their citation patterns"
            ]
        
        return analysis

