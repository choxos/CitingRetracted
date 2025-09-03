#!/usr/bin/env python3
"""
Text Analysis Utilities for Journal Content Analysis
Advanced NLP techniques for content quality assessment
"""

import re
from typing import Dict, List, Tuple, Optional
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from textblob import TextBlob
from textstat import (
    flesch_reading_ease, flesch_kincaid_grade, 
    automated_readability_index, coleman_liau_index
)
import langdetect
from collections import Counter
import string

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('chunkers/maxent_ne_chunker')
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class TextAnalyzer:
    """Advanced text analysis for journal content quality assessment"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Predatory journal warning phrases
        self.predatory_indicators = {
            'high_risk': [
                'guaranteed acceptance', 'rapid publication within days',
                'nobel laureate editor', 'fake impact factor', 
                'pay only after acceptance', 'bitcoin payment accepted'
            ],
            'medium_risk': [
                'fast track publication', 'within 24 hours',
                'immediate publication', 'no peer review required',
                'instant acceptance', 'publish immediately'
            ],
            'low_risk': [
                'quick publication', 'rapid review', 'fast processing',
                'speedy publication', 'accelerated review'
            ]
        }
        
        # Academic quality indicators
        self.quality_indicators = {
            'high_quality': [
                'rigorous peer review', 'double blind review',
                'editorial board', 'impact factor', 'indexed in pubmed',
                'scopus indexed', 'web of science'
            ],
            'medium_quality': [
                'peer reviewed', 'editorial review', 'manuscript review',
                'quality control', 'academic standards'
            ]
        }
        
        # Suspicious language patterns
        self.suspicious_patterns = [
            r'impact\s+factor\s+will\s+be\s+\d+',  # Promising future IF
            r'guarantee[ds]?\s+(acceptance|publication)',  # Guaranteed acceptance
            r'within\s+\d+\s+(hours?|days?)\s+publication',  # Unrealistic timelines
            r'pay\s+(only\s+)?after\s+(acceptance|publication)',  # Payment after acceptance
            r'(bitcoin|cryptocurrency)\s+(payment|accepted)',  # Crypto payments
        ]
    
    def analyze_text_comprehensive(self, text: str) -> Dict:
        """Comprehensive text analysis returning multiple metrics"""
        if not text or len(text.strip()) < 10:
            return self._empty_analysis()
        
        analysis = {
            'basic_metrics': self._calculate_basic_metrics(text),
            'readability_metrics': self._calculate_readability(text),
            'language_analysis': self._analyze_language(text),
            'quality_assessment': self._assess_content_quality(text),
            'predatory_indicators': self._detect_predatory_indicators(text),
            'academic_quality': self._assess_academic_quality(text),
            'sentiment_analysis': self._analyze_sentiment(text),
            'keyword_analysis': self._extract_keywords(text),
            'overall_score': 0
        }
        
        # Calculate overall quality score
        analysis['overall_score'] = self._calculate_overall_score(analysis)
        
        return analysis
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis for invalid input"""
        return {
            'basic_metrics': {},
            'readability_metrics': {},
            'language_analysis': {},
            'quality_assessment': {},
            'predatory_indicators': {},
            'academic_quality': {},
            'sentiment_analysis': {},
            'keyword_analysis': {},
            'overall_score': 0
        }
    
    def _calculate_basic_metrics(self, text: str) -> Dict:
        """Calculate basic text metrics"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        
        # Filter out punctuation
        words_no_punct = [word for word in words if word not in string.punctuation]
        
        # Character analysis
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Word analysis
        word_count = len(words_no_punct)
        unique_words = len(set(words_no_punct))
        avg_word_length = sum(len(word) for word in words_no_punct) / word_count if word_count > 0 else 0
        
        # Sentence analysis
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Paragraph analysis (rough estimate)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        return {
            'character_count': char_count,
            'character_count_no_spaces': char_count_no_spaces,
            'word_count': word_count,
            'unique_word_count': unique_words,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'lexical_diversity': round(unique_words / word_count, 3) if word_count > 0 else 0
        }
    
    def _calculate_readability(self, text: str) -> Dict:
        """Calculate various readability metrics"""
        try:
            return {
                'flesch_reading_ease': round(flesch_reading_ease(text), 2),
                'flesch_kincaid_grade': round(flesch_kincaid_grade(text), 2),
                'automated_readability_index': round(automated_readability_index(text), 2),
                'coleman_liau_index': round(coleman_liau_index(text), 2),
                'readability_interpretation': self._interpret_readability(flesch_reading_ease(text))
            }
        except Exception as e:
            return {
                'error': f"Readability calculation failed: {str(e)}",
                'flesch_reading_ease': 0,
                'readability_interpretation': 'unknown'
            }
    
    def _interpret_readability(self, flesch_score: float) -> str:
        """Interpret Flesch Reading Ease score"""
        if flesch_score >= 90:
            return "very_easy"
        elif flesch_score >= 80:
            return "easy"
        elif flesch_score >= 70:
            return "fairly_easy"
        elif flesch_score >= 60:
            return "standard"
        elif flesch_score >= 50:
            return "fairly_difficult"
        elif flesch_score >= 30:
            return "difficult"
        else:
            return "very_difficult"
    
    def _analyze_language(self, text: str) -> Dict:
        """Analyze language characteristics"""
        try:
            # Language detection
            detected_language = langdetect.detect(text[:1000])  # Use first 1000 chars
            confidence = langdetect.detect_langs(text[:1000])[0].prob
            
            # Grammar and spelling analysis using TextBlob
            blob = TextBlob(text[:5000])  # Limit for performance
            
            # POS tagging analysis
            words = word_tokenize(text.lower())
            words_no_punct = [word for word in words if word.isalpha()]
            pos_tags = pos_tag(words_no_punct[:100])  # Limit for performance
            
            pos_counts = Counter([tag for word, tag in pos_tags])
            
            return {
                'detected_language': detected_language,
                'language_confidence': round(confidence, 3),
                'is_english': detected_language == 'en',
                'pos_distribution': dict(pos_counts.most_common(10)),
                'estimated_spelling_errors': self._estimate_spelling_errors(text),
                'sentence_structure_score': self._analyze_sentence_structure(text)
            }
            
        except Exception as e:
            return {
                'error': f"Language analysis failed: {str(e)}",
                'detected_language': 'unknown',
                'is_english': False
            }
    
    def _estimate_spelling_errors(self, text: str) -> int:
        """Estimate number of spelling errors (basic heuristic)"""
        words = word_tokenize(text.lower())
        words_alpha = [word for word in words if word.isalpha()]
        
        # Common typos and patterns
        error_patterns = [
            r'\b(recieve|seperate|occured|teh|adn|hte|thier|thier|youre|its a)\b',
            r'\b\w*([aeiou])\1{2,}\w*\b',  # Repeated vowels
            r'\b\w*([bcdfghjklmnpqrstvwxyz])\1{2,}\w*\b',  # Repeated consonants
        ]
        
        error_count = 0
        full_text = ' '.join(words_alpha)
        
        for pattern in error_patterns:
            error_count += len(re.findall(pattern, full_text, re.IGNORECASE))
        
        return error_count
    
    def _analyze_sentence_structure(self, text: str) -> float:
        """Analyze sentence structure quality (0-100)"""
        sentences = sent_tokenize(text)
        
        if not sentences:
            return 0
        
        score = 0
        
        # Check sentence length distribution
        lengths = [len(word_tokenize(sentence)) for sentence in sentences]
        avg_length = sum(lengths) / len(lengths)
        
        # Optimal sentence length is around 15-20 words
        if 15 <= avg_length <= 20:
            score += 30
        elif 10 <= avg_length <= 25:
            score += 20
        elif avg_length > 5:
            score += 10
        
        # Check for sentence variety
        length_variety = len(set(lengths)) / len(lengths) if lengths else 0
        score += length_variety * 30
        
        # Check for proper punctuation
        proper_endings = sum(1 for s in sentences if s.strip().endswith(('.', '!', '?')))
        punctuation_score = (proper_endings / len(sentences)) * 40
        score += punctuation_score
        
        return min(score, 100)
    
    def _assess_content_quality(self, text: str) -> Dict:
        """Assess overall content quality"""
        quality_score = 0
        issues = []
        
        # Content length assessment
        word_count = len(word_tokenize(text))
        
        if word_count < 100:
            issues.append("Very short content")
            quality_score -= 20
        elif word_count < 300:
            issues.append("Short content")
            quality_score -= 10
        elif word_count > 1000:
            quality_score += 20
        elif word_count > 500:
            quality_score += 10
        
        # Repetition check
        words = word_tokenize(text.lower())
        word_freq = Counter(words)
        most_common = word_freq.most_common(5)
        
        if most_common and most_common[0][1] > len(words) * 0.1:  # If most common word is >10%
            issues.append("High word repetition")
            quality_score -= 15
        
        # Check for all caps (shouting)
        caps_sentences = [s for s in sent_tokenize(text) if s.isupper() and len(s) > 10]
        if caps_sentences:
            issues.append("Excessive capitalization")
            quality_score -= 10
        
        # Check for multiple consecutive punctuation
        if re.search(r'[.!?]{3,}', text):
            issues.append("Excessive punctuation")
            quality_score -= 5
        
        return {
            'quality_score': max(quality_score + 50, 0),  # Base score of 50
            'issues': issues,
            'content_density': self._calculate_content_density(text)
        }
    
    def _calculate_content_density(self, text: str) -> float:
        """Calculate information density of the text"""
        words = word_tokenize(text.lower())
        words_no_stop = [word for word in words if word not in self.stop_words and word.isalpha()]
        
        if not words:
            return 0
        
        # Information density = non-stopwords / total words
        return len(words_no_stop) / len(words)
    
    def _detect_predatory_indicators(self, text: str) -> Dict:
        """Detect predatory publishing indicators in text"""
        text_lower = text.lower()
        indicators_found = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'suspicious_patterns': [],
            'risk_score': 0
        }
        
        # Check for predatory phrases
        for risk_level, phrases in self.predatory_indicators.items():
            for phrase in phrases:
                if phrase in text_lower:
                    indicators_found[risk_level].append(phrase)
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                indicators_found['suspicious_patterns'].extend(matches)
        
        # Calculate risk score
        risk_score = 0
        risk_score += len(indicators_found['high_risk']) * 30
        risk_score += len(indicators_found['medium_risk']) * 15
        risk_score += len(indicators_found['low_risk']) * 5
        risk_score += len(indicators_found['suspicious_patterns']) * 20
        
        indicators_found['risk_score'] = min(risk_score, 100)
        
        return indicators_found
    
    def _assess_academic_quality(self, text: str) -> Dict:
        """Assess academic quality indicators"""
        text_lower = text.lower()
        quality_indicators = {
            'high_quality_found': [],
            'medium_quality_found': [],
            'academic_terms_count': 0,
            'quality_score': 0
        }
        
        # Check for quality indicators
        for level, terms in self.quality_indicators.items():
            for term in terms:
                if term in text_lower:
                    quality_indicators[f'{level}_found'].append(term)
        
        # Count academic terms
        academic_terms = [
            'research', 'study', 'analysis', 'methodology', 'publication',
            'journal', 'peer review', 'academic', 'scholarly', 'citation',
            'manuscript', 'author', 'editor', 'reviewer', 'bibliography'
        ]
        
        academic_count = sum(1 for term in academic_terms if term in text_lower)
        quality_indicators['academic_terms_count'] = academic_count
        
        # Calculate quality score
        quality_score = 0
        quality_score += len(quality_indicators['high_quality_found']) * 15
        quality_score += len(quality_indicators['medium_quality_found']) * 10
        quality_score += min(academic_count * 2, 30)  # Max 30 points from academic terms
        
        quality_indicators['quality_score'] = min(quality_score, 100)
        
        return quality_indicators
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of the text"""
        try:
            blob = TextBlob(text[:2000])  # Limit for performance
            
            return {
                'polarity': round(blob.sentiment.polarity, 3),  # -1 to 1
                'subjectivity': round(blob.sentiment.subjectivity, 3),  # 0 to 1
                'sentiment_interpretation': self._interpret_sentiment(blob.sentiment.polarity)
            }
        except Exception as e:
            return {
                'error': f"Sentiment analysis failed: {str(e)}",
                'polarity': 0,
                'subjectivity': 0.5
            }
    
    def _interpret_sentiment(self, polarity: float) -> str:
        """Interpret sentiment polarity"""
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _extract_keywords(self, text: str) -> Dict:
        """Extract important keywords and phrases"""
        words = word_tokenize(text.lower())
        words_filtered = [word for word in words if word.isalpha() and word not in self.stop_words]
        
        # Most frequent words
        word_freq = Counter(words_filtered)
        top_words = word_freq.most_common(10)
        
        # Extract potential journal/publisher names
        sentences = sent_tokenize(text)
        journal_patterns = [
            r'published\s+(?:in|by)\s+([A-Z][a-zA-Z\s&]+(?:Journal|Review|Magazine|Quarterly))',
            r'([A-Z][a-zA-Z\s&]+(?:Journal|Review|Magazine|Quarterly))',
            r'(International\s+[A-Z][a-zA-Z\s]+)',
            r'(Journal\s+of\s+[A-Z][a-zA-Z\s]+)'
        ]
        
        potential_journals = []
        for pattern in journal_patterns:
            matches = re.findall(pattern, text)
            potential_journals.extend(matches)
        
        return {
            'top_words': top_words,
            'potential_journal_names': list(set(potential_journals)),
            'word_diversity': len(set(words_filtered)) / len(words_filtered) if words_filtered else 0
        }
    
    def _calculate_overall_score(self, analysis: Dict) -> float:
        """Calculate overall text quality score (0-100)"""
        scores = []
        weights = []
        
        # Basic metrics weight
        if 'basic_metrics' in analysis:
            basic = analysis['basic_metrics']
            basic_score = 0
            
            # Word count scoring
            word_count = basic.get('word_count', 0)
            if word_count > 1000:
                basic_score += 30
            elif word_count > 500:
                basic_score += 20
            elif word_count > 200:
                basic_score += 10
            
            # Lexical diversity scoring
            diversity = basic.get('lexical_diversity', 0)
            basic_score += diversity * 30
            
            # Sentence structure scoring
            avg_sent_length = basic.get('avg_sentence_length', 0)
            if 15 <= avg_sent_length <= 25:
                basic_score += 20
            elif 10 <= avg_sent_length <= 30:
                basic_score += 10
            
            scores.append(min(basic_score, 100))
            weights.append(0.2)
        
        # Readability weight
        if 'readability_metrics' in analysis:
            readability = analysis['readability_metrics'].get('flesch_reading_ease', 0)
            if readability >= 60:
                readability_score = 100
            elif readability >= 30:
                readability_score = 70
            elif readability >= 0:
                readability_score = 40
            else:
                readability_score = 20
            
            scores.append(readability_score)
            weights.append(0.15)
        
        # Language quality weight
        if 'language_analysis' in analysis:
            lang_score = 0
            if analysis['language_analysis'].get('is_english', False):
                lang_score += 40
            
            lang_score += analysis['language_analysis'].get('sentence_structure_score', 0) * 0.6
            
            # Penalty for spelling errors
            errors = analysis['language_analysis'].get('estimated_spelling_errors', 0)
            word_count = analysis.get('basic_metrics', {}).get('word_count', 1)
            error_rate = errors / word_count
            if error_rate < 0.01:
                lang_score += 0
            elif error_rate < 0.03:
                lang_score -= 10
            else:
                lang_score -= 20
            
            scores.append(max(lang_score, 0))
            weights.append(0.2)
        
        # Content quality weight
        if 'quality_assessment' in analysis:
            content_score = analysis['quality_assessment'].get('quality_score', 50)
            scores.append(content_score)
            weights.append(0.15)
        
        # Academic quality weight
        if 'academic_quality' in analysis:
            academic_score = analysis['academic_quality'].get('quality_score', 0)
            scores.append(academic_score)
            weights.append(0.15)
        
        # Predatory indicators penalty
        if 'predatory_indicators' in analysis:
            predatory_risk = analysis['predatory_indicators'].get('risk_score', 0)
            predatory_penalty = 100 - predatory_risk  # Convert risk to quality score
            scores.append(max(predatory_penalty, 0))
            weights.append(0.15)
        
        # Calculate weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        else:
            overall_score = 0
        
        return round(min(overall_score, 100), 2)


