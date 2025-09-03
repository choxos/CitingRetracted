#!/usr/bin/env python3
"""
Feature Extraction for Predatory Journal Detection
Convert scraped data into machine learning features
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

class FeatureExtractor:
    """Extract and engineer features from scraped journal data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Feature categories
        self.feature_categories = {
            'website_quality': [
                'technical_score', 'design_score', 'content_score', 'overall_score',
                'response_time', 'page_size', 'has_ssl', 'mobile_responsive'
            ],
            'editorial_board': [
                'board_size', 'has_editor_in_chief', 'board_quality_score',
                'member_completeness_ratio', 'affiliation_diversity'
            ],
            'submission_process': [
                'has_guidelines', 'peer_review_mentioned', 'timeline_mentioned',
                'review_timeline_days', 'submission_quality_score'
            ],
            'contact_information': [
                'has_email', 'has_phone', 'has_address', 'contact_quality_score',
                'email_count', 'phone_count'
            ],
            'publication_fees': [
                'has_fees', 'fees_amount', 'suspicious_payment', 'fees_quality_score'
            ],
            'content_quality': [
                'word_count', 'readability_score', 'grammar_errors', 'language_quality',
                'content_density', 'academic_terms_count'
            ],
            'domain_analysis': [
                'domain_age_days', 'domain_risk_score', 'suspicious_tld',
                'legitimate_publisher', 'academic_domain', 'ssl_valid'
            ],
            'predatory_indicators': [
                'high_risk_indicators', 'medium_risk_indicators', 'low_risk_indicators',
                'suspicious_patterns', 'predatory_risk_score'
            ],
            'bibliometric': [
                'claimed_impact_factor', 'issn_count', 'publisher_legitimacy',
                'indexing_claims'
            ]
        }
    
    def extract_features(self, scraped_data: Dict) -> Dict:
        """
        Extract comprehensive feature set from scraped journal data
        
        Args:
            scraped_data: Dictionary containing scraped journal information
            
        Returns:
            Dictionary containing extracted features
        """
        features = {
            'journal_url': scraped_data.get('url', ''),
            'scrape_timestamp': scraped_data.get('scrape_timestamp', ''),
            'scrape_success': scraped_data.get('scrape_success', False)
        }
        
        try:
            # Website quality features
            website_features = self._extract_website_features(scraped_data)
            features.update(website_features)
            
            # Editorial board features
            editorial_features = self._extract_editorial_features(scraped_data)
            features.update(editorial_features)
            
            # Submission process features
            submission_features = self._extract_submission_features(scraped_data)
            features.update(submission_features)
            
            # Contact information features
            contact_features = self._extract_contact_features(scraped_data)
            features.update(contact_features)
            
            # Publication fees features
            fees_features = self._extract_fees_features(scraped_data)
            features.update(fees_features)
            
            # Content quality features
            content_features = self._extract_content_features(scraped_data)
            features.update(content_features)
            
            # Domain analysis features
            domain_features = self._extract_domain_features(scraped_data)
            features.update(domain_features)
            
            # Predatory indicators features
            predatory_features = self._extract_predatory_features(scraped_data)
            features.update(predatory_features)
            
            # Bibliometric features
            biblio_features = self._extract_bibliometric_features(scraped_data)
            features.update(biblio_features)
            
            # Composite features
            composite_features = self._calculate_composite_features(features)
            features.update(composite_features)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            features['extraction_error'] = str(e)
        
        return features
    
    def _extract_website_features(self, data: Dict) -> Dict:
        """Extract website quality features"""
        features = {}
        
        quality_metrics = data.get('quality_metrics', {})
        
        # Basic website quality scores
        features['technical_score'] = quality_metrics.get('technical_score', 0)
        features['design_score'] = quality_metrics.get('design_score', 0)
        features['content_score'] = quality_metrics.get('content_score', 0)
        features['overall_score'] = quality_metrics.get('overall_score', 0)
        
        # Technical characteristics
        features['response_time'] = data.get('response_time', 0)
        features['page_size'] = data.get('page_size', 0)
        features['has_ssl'] = 1 if data.get('has_ssl', False) else 0
        features['status_code'] = data.get('status_code', 404)
        
        # Derived features
        features['page_size_kb'] = features['page_size'] / 1024 if features['page_size'] else 0
        features['fast_response'] = 1 if features['response_time'] < 2.0 else 0
        features['successful_response'] = 1 if 200 <= features['status_code'] < 300 else 0
        
        # Website issues count
        issues = quality_metrics.get('issues', [])
        features['website_issues_count'] = len(issues)
        features['mobile_responsive'] = 0 if 'Not mobile responsive' in issues else 1
        
        return features
    
    def _extract_editorial_features(self, data: Dict) -> Dict:
        """Extract editorial board features"""
        features = {}
        
        editorial_info = data.get('editorial_board', {})
        
        # Basic editorial features
        features['board_size'] = editorial_info.get('board_size', 0)
        features['has_editor_in_chief'] = 1 if editorial_info.get('editor_in_chief') else 0
        features['board_quality_score'] = editorial_info.get('quality_score', 0)
        
        # Board composition analysis
        members = editorial_info.get('members', [])
        
        if members:
            # Completeness analysis
            complete_members = sum(1 for member in members 
                                 if member.get('name') and member.get('affiliation'))
            features['member_completeness_ratio'] = complete_members / len(members)
            
            # Diversity analysis
            affiliations = set(member.get('affiliation', '').lower() 
                             for member in members if member.get('affiliation'))
            features['affiliation_diversity'] = len(affiliations) / len(members) if members else 0
            
            # Email availability
            emails = sum(1 for member in members if member.get('email'))
            features['board_email_ratio'] = emails / len(members)
            
            # Title analysis
            titles = [member.get('title', '').lower() for member in members if member.get('title')]
            academic_titles = sum(1 for title in titles 
                                if any(term in title for term in ['professor', 'dr.', 'ph.d']))
            features['academic_title_ratio'] = academic_titles / len(members) if members else 0
        else:
            features['member_completeness_ratio'] = 0
            features['affiliation_diversity'] = 0
            features['board_email_ratio'] = 0
            features['academic_title_ratio'] = 0
        
        # Board size categories
        features['small_board'] = 1 if features['board_size'] < 5 else 0
        features['medium_board'] = 1 if 5 <= features['board_size'] < 15 else 0
        features['large_board'] = 1 if features['board_size'] >= 15 else 0
        
        return features
    
    def _extract_submission_features(self, data: Dict) -> Dict:
        """Extract submission process features"""
        features = {}
        
        submission_info = data.get('submission_info', {})
        
        # Basic submission features
        features['has_guidelines'] = 1 if submission_info.get('has_guidelines', False) else 0
        features['peer_review_mentioned'] = 1 if submission_info.get('peer_review_mentioned', False) else 0
        features['timeline_mentioned'] = 1 if submission_info.get('timeline_mentioned', False) else 0
        features['submission_quality_score'] = submission_info.get('quality_score', 0)
        
        # Timeline analysis
        review_timeline = submission_info.get('review_timeline')
        if review_timeline:
            try:
                # Convert timeline to days
                timeline_str = str(review_timeline).lower()
                if 'week' in timeline_str:
                    features['review_timeline_days'] = int(re.findall(r'\d+', timeline_str)[0]) * 7
                elif 'day' in timeline_str:
                    features['review_timeline_days'] = int(re.findall(r'\d+', timeline_str)[0])
                else:
                    features['review_timeline_days'] = 30  # Default assumption
            except:
                features['review_timeline_days'] = 30
        else:
            features['review_timeline_days'] = 0
        
        # Timeline categories
        features['very_fast_review'] = 1 if 0 < features['review_timeline_days'] < 7 else 0
        features['fast_review'] = 1 if 7 <= features['review_timeline_days'] < 30 else 0
        features['normal_review'] = 1 if 30 <= features['review_timeline_days'] < 90 else 0
        features['slow_review'] = 1 if features['review_timeline_days'] >= 90 else 0
        
        return features
    
    def _extract_contact_features(self, data: Dict) -> Dict:
        """Extract contact information features"""
        features = {}
        
        contact_info = data.get('contact_info', {})
        
        # Basic contact features
        features['has_email'] = 1 if contact_info.get('has_email', False) else 0
        features['has_phone'] = 1 if contact_info.get('has_phone', False) else 0
        features['has_address'] = 1 if contact_info.get('has_address', False) else 0
        features['contact_quality_score'] = contact_info.get('quality_score', 0)
        
        # Contact method counts
        features['email_count'] = len(contact_info.get('emails', []))
        features['phone_count'] = len(contact_info.get('phones', []))
        features['address_count'] = len(contact_info.get('addresses', []))
        
        # Contact completeness
        contact_methods = sum([features['has_email'], features['has_phone'], features['has_address']])
        features['contact_methods_count'] = contact_methods
        features['complete_contact'] = 1 if contact_methods >= 2 else 0
        
        return features
    
    def _extract_fees_features(self, data: Dict) -> Dict:
        """Extract publication fees features"""
        features = {}
        
        fees_info = data.get('fees_info', {})
        
        # Basic fees features
        features['has_fees'] = 1 if fees_info.get('has_fees', False) else 0
        features['suspicious_payment'] = 1 if fees_info.get('suspicious_payment', False) else 0
        features['fees_quality_score'] = fees_info.get('quality_score', 0)
        
        # Fee amount analysis
        fees_amount = fees_info.get('fees_amount')
        if fees_amount:
            try:
                amount = float(str(fees_amount).replace(',', ''))
                features['fees_amount'] = amount
                
                # Fee categories
                features['low_fee'] = 1 if amount < 500 else 0
                features['medium_fee'] = 1 if 500 <= amount < 1500 else 0
                features['high_fee'] = 1 if 1500 <= amount < 3000 else 0
                features['very_high_fee'] = 1 if amount >= 3000 else 0
            except:
                features['fees_amount'] = 0
                features['low_fee'] = 0
                features['medium_fee'] = 0
                features['high_fee'] = 0
                features['very_high_fee'] = 0
        else:
            features['fees_amount'] = 0
            features['low_fee'] = 0
            features['medium_fee'] = 0
            features['high_fee'] = 0
            features['very_high_fee'] = 0
        
        # Currency analysis
        currency = fees_info.get('currency', '').upper()
        features['usd_fees'] = 1 if currency in ['USD', '$'] else 0
        features['eur_fees'] = 1 if currency in ['EUR', '€'] else 0
        features['gbp_fees'] = 1 if currency in ['GBP', '£'] else 0
        
        return features
    
    def _extract_content_features(self, data: Dict) -> Dict:
        """Extract content quality features"""
        features = {}
        
        content_quality = data.get('content_quality', {})
        
        # Basic content metrics
        basic_metrics = content_quality.get('basic_metrics', {})
        features['word_count'] = basic_metrics.get('word_count', 0)
        features['sentence_count'] = basic_metrics.get('sentence_count', 0)
        features['paragraph_count'] = basic_metrics.get('paragraph_count', 0)
        features['avg_word_length'] = basic_metrics.get('avg_word_length', 0)
        features['avg_sentence_length'] = basic_metrics.get('avg_sentence_length', 0)
        features['lexical_diversity'] = basic_metrics.get('lexical_diversity', 0)
        
        # Readability metrics
        readability = content_quality.get('readability_metrics', {})
        features['readability_score'] = readability.get('flesch_reading_ease', 0)
        features['grade_level'] = readability.get('flesch_kincaid_grade', 0)
        
        # Language analysis
        language_analysis = content_quality.get('language_analysis', {})
        features['is_english'] = 1 if language_analysis.get('is_english', False) else 0
        features['language_confidence'] = language_analysis.get('language_confidence', 0)
        features['grammar_errors'] = language_analysis.get('estimated_spelling_errors', 0)
        features['sentence_structure_score'] = language_analysis.get('sentence_structure_score', 0)
        
        # Content quality assessment
        quality_assessment = content_quality.get('quality_assessment', {})
        features['content_quality_score'] = quality_assessment.get('quality_score', 0)
        features['content_density'] = quality_assessment.get('content_density', 0)
        
        # Academic quality
        academic_quality = content_quality.get('academic_quality', {})
        features['academic_terms_count'] = academic_quality.get('academic_terms_count', 0)
        features['academic_quality_score'] = academic_quality.get('quality_score', 0)
        
        # Content categories
        features['very_short_content'] = 1 if features['word_count'] < 200 else 0
        features['short_content'] = 1 if 200 <= features['word_count'] < 500 else 0
        features['medium_content'] = 1 if 500 <= features['word_count'] < 1000 else 0
        features['long_content'] = 1 if features['word_count'] >= 1000 else 0
        
        # Grammar error rate
        if features['word_count'] > 0:
            features['grammar_error_rate'] = features['grammar_errors'] / features['word_count']
        else:
            features['grammar_error_rate'] = 0
        
        return features
    
    def _extract_domain_features(self, data: Dict) -> Dict:
        """Extract domain analysis features"""
        features = {}
        
        technical_analysis = data.get('technical_analysis', {})
        domain_info = technical_analysis.get('domain_info', {})
        
        # Basic domain features
        features['domain_risk_score'] = domain_info.get('risk_score', 50)
        features['is_suspicious_domain'] = 1 if domain_info.get('is_suspicious', False) else 0
        
        # WHOIS features
        whois_info = domain_info.get('whois_info', {})
        features['domain_age_days'] = whois_info.get('domain_age_days', 0)
        features['privacy_protected'] = 1 if whois_info.get('privacy_protected', False) else 0
        features['suspicious_registrar'] = 1 if whois_info.get('suspicious_registrar', False) else 0
        
        # Domain characteristics
        features['suspicious_tld'] = 1 if domain_info.get('suspicious_tld', False) else 0
        features['academic_domain'] = 1 if domain_info.get('academic_domain', False) else 0
        features['legitimate_publisher'] = 1 if domain_info.get('legitimate_publisher', False) else 0
        features['typosquatting_risk'] = 1 if domain_info.get('typosquatting_risk', False) else 0
        
        # SSL features
        ssl_info = domain_info.get('ssl_info', {})
        features['ssl_valid'] = 1 if ssl_info.get('valid', False) else 0
        features['ssl_self_signed'] = 1 if ssl_info.get('self_signed', False) else 0
        
        # Age categories
        if features['domain_age_days'] > 0:
            features['very_new_domain'] = 1 if features['domain_age_days'] < 30 else 0
            features['new_domain'] = 1 if 30 <= features['domain_age_days'] < 365 else 0
            features['established_domain'] = 1 if 365 <= features['domain_age_days'] < 365*3 else 0
            features['old_domain'] = 1 if features['domain_age_days'] >= 365*3 else 0
        else:
            features['very_new_domain'] = 0
            features['new_domain'] = 0
            features['established_domain'] = 0
            features['old_domain'] = 0
        
        return features
    
    def _extract_predatory_features(self, data: Dict) -> Dict:
        """Extract predatory indicators features"""
        features = {}
        
        content_quality = data.get('content_quality', {})
        predatory_indicators = content_quality.get('predatory_indicators', {})
        
        # Predatory indicator counts
        features['high_risk_indicators'] = len(predatory_indicators.get('high_risk', []))
        features['medium_risk_indicators'] = len(predatory_indicators.get('medium_risk', []))
        features['low_risk_indicators'] = len(predatory_indicators.get('low_risk', []))
        features['suspicious_patterns'] = len(predatory_indicators.get('suspicious_patterns', []))
        features['predatory_risk_score'] = predatory_indicators.get('risk_score', 0)
        
        # Total indicators
        features['total_predatory_indicators'] = (
            features['high_risk_indicators'] + 
            features['medium_risk_indicators'] + 
            features['low_risk_indicators']
        )
        
        # Risk categories
        features['high_predatory_risk'] = 1 if features['predatory_risk_score'] > 70 else 0
        features['medium_predatory_risk'] = 1 if 30 < features['predatory_risk_score'] <= 70 else 0
        features['low_predatory_risk'] = 1 if features['predatory_risk_score'] <= 30 else 0
        
        return features
    
    def _extract_bibliometric_features(self, data: Dict) -> Dict:
        """Extract bibliometric features"""
        features = {}
        
        metadata = data.get('metadata', {})
        
        # Impact factor claims
        claimed_if = metadata.get('claimed_impact_factor')
        if claimed_if:
            try:
                features['claimed_impact_factor'] = float(claimed_if)
                features['has_impact_factor_claim'] = 1
                features['high_if_claim'] = 1 if features['claimed_impact_factor'] > 10 else 0
                features['suspicious_if_claim'] = 1 if features['claimed_impact_factor'] > 20 else 0
            except:
                features['claimed_impact_factor'] = 0
                features['has_impact_factor_claim'] = 0
                features['high_if_claim'] = 0
                features['suspicious_if_claim'] = 0
        else:
            features['claimed_impact_factor'] = 0
            features['has_impact_factor_claim'] = 0
            features['high_if_claim'] = 0
            features['suspicious_if_claim'] = 0
        
        # ISSN analysis
        issns = metadata.get('issns', [])
        features['issn_count'] = len(issns)
        features['has_issn'] = 1 if features['issn_count'] > 0 else 0
        features['multiple_issns'] = 1 if features['issn_count'] > 1 else 0
        
        # Publisher information
        publisher = metadata.get('publisher', '').lower()
        features['has_publisher_info'] = 1 if publisher else 0
        
        # Known publishers check (simplified)
        known_publishers = ['elsevier', 'springer', 'wiley', 'nature', 'taylor', 'sage']
        features['known_publisher'] = 1 if any(pub in publisher for pub in known_publishers) else 0
        
        return features
    
    def _calculate_composite_features(self, features: Dict) -> Dict:
        """Calculate composite features from individual features"""
        composite = {}
        
        # Overall quality composite
        quality_scores = [
            features.get('overall_score', 0),
            features.get('board_quality_score', 0),
            features.get('submission_quality_score', 0),
            features.get('contact_quality_score', 0),
            features.get('content_quality_score', 0),
            features.get('academic_quality_score', 0)
        ]
        composite['avg_quality_score'] = np.mean(quality_scores)
        composite['min_quality_score'] = np.min(quality_scores)
        composite['quality_score_std'] = np.std(quality_scores)
        
        # Risk composite (inverse of security scores)
        risk_scores = [
            features.get('domain_risk_score', 50),
            features.get('predatory_risk_score', 0),
            100 - features.get('fees_quality_score', 50)  # Inverse fees quality
        ]
        composite['avg_risk_score'] = np.mean(risk_scores)
        composite['max_risk_score'] = np.max(risk_scores)
        
        # Completeness composite
        completeness_indicators = [
            features.get('has_email', 0),
            features.get('has_phone', 0),
            features.get('has_address', 0),
            features.get('has_guidelines', 0),
            features.get('peer_review_mentioned', 0),
            features.get('has_editor_in_chief', 0),
            features.get('has_publisher_info', 0),
            features.get('has_issn', 0)
        ]
        composite['completeness_score'] = np.mean(completeness_indicators) * 100
        
        # Technical quality composite
        technical_indicators = [
            features.get('has_ssl', 0),
            features.get('mobile_responsive', 0),
            features.get('successful_response', 0),
            features.get('fast_response', 0),
            features.get('ssl_valid', 0)
        ]
        composite['technical_quality'] = np.mean(technical_indicators) * 100
        
        # Legitimacy composite
        legitimacy_indicators = [
            features.get('legitimate_publisher', 0),
            features.get('academic_domain', 0),
            features.get('known_publisher', 0),
            1 - features.get('suspicious_tld', 0),  # Inverse
            1 - features.get('typosquatting_risk', 0),  # Inverse
            features.get('established_domain', 0)
        ]
        composite['legitimacy_score'] = np.mean(legitimacy_indicators) * 100
        
        return composite
    
    def prepare_ml_dataset(self, features_list: List[Dict]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare feature dataset for machine learning
        
        Args:
            features_list: List of feature dictionaries
            
        Returns:
            Tuple of (DataFrame, feature_names)
        """
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        
        # Select numerical features for ML
        numerical_features = []
        for category, feature_names in self.feature_categories.items():
            for feature in feature_names:
                if feature in df.columns:
                    numerical_features.append(feature)
        
        # Add composite features
        composite_features = [col for col in df.columns if 'composite' in col.lower() or 
                            col.startswith(('avg_', 'min_', 'max_', 'completeness_', 'technical_', 'legitimacy_'))]
        numerical_features.extend(composite_features)
        
        # Handle missing values
        ml_df = df[numerical_features].fillna(0)
        
        # Remove constant features
        non_constant_features = []
        for feature in numerical_features:
            if feature in ml_df.columns and ml_df[feature].nunique() > 1:
                non_constant_features.append(feature)
        
        ml_df = ml_df[non_constant_features]
        
        self.logger.info(f"Prepared ML dataset with {len(ml_df)} samples and {len(non_constant_features)} features")
        
        return ml_df, non_constant_features

