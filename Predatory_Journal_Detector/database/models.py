#!/usr/bin/env python3
"""
Database models for Predatory Journal Detector
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, List, Optional

Base = declarative_base()

class Journal(Base):
    """Main journal information model"""
    __tablename__ = 'journals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=False, unique=True)
    issn = Column(String(20), index=True)
    eissn = Column(String(20), index=True)
    
    # Publisher information
    publisher = Column(String(300))
    publisher_country = Column(String(100))
    publisher_address = Column(Text)
    
    # Editorial information
    editor_in_chief = Column(String(300))
    editorial_board_size = Column(Integer)
    editorial_board_info = Column(JSON)
    
    # Publication details
    first_publication_year = Column(Integer)
    publication_frequency = Column(String(100))
    article_processing_charge = Column(Float)
    currency = Column(String(10))
    
    # Indexing information
    pubmed_indexed = Column(Boolean, default=False)
    scopus_indexed = Column(Boolean, default=False)
    wos_indexed = Column(Boolean, default=False)
    claimed_impact_factor = Column(Float)
    actual_impact_factor = Column(Float)
    
    # Website analysis results
    website_quality_score = Column(Float)
    content_quality_score = Column(Float)
    technical_quality_score = Column(Float)
    
    # Bibliometric data
    total_publications = Column(Integer, default=0)
    total_citations = Column(Integer, default=0)
    h_index = Column(Integer, default=0)
    self_citation_rate = Column(Float, default=0.0)
    
    # Predatory assessment
    predatory_score = Column(Float)
    risk_level = Column(String(50))
    is_predatory = Column(Boolean)
    confidence_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_scraped = Column(DateTime)
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'issn': self.issn,
            'eissn': self.eissn,
            'publisher': self.publisher,
            'predatory_score': self.predatory_score,
            'risk_level': self.risk_level,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WebsiteContent(Base):
    """Store scraped website content"""
    __tablename__ = 'website_content'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    
    # Page content
    title = Column(String(1000))
    html_content = Column(Text)
    text_content = Column(Text)
    
    # Technical details
    response_time = Column(Float)
    status_code = Column(Integer)
    has_ssl = Column(Boolean)
    page_size = Column(Integer)
    
    # Content analysis
    word_count = Column(Integer)
    language = Column(String(10))
    grammar_errors = Column(Integer)
    spelling_errors = Column(Integer)
    
    # Metadata
    scraped_at = Column(DateTime, default=func.now())
    scrape_success = Column(Boolean, default=True)
    error_message = Column(Text)

class EditorialBoard(Base):
    """Editorial board member information"""
    __tablename__ = 'editorial_board'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, nullable=False, index=True)
    
    name = Column(String(300), nullable=False)
    title = Column(String(500))
    affiliation = Column(String(500))
    country = Column(String(100))
    email = Column(String(300))
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(100))
    
    # Academic credentials
    h_index = Column(Integer)
    publication_count = Column(Integer)
    citation_count = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())

class JournalMetrics(Base):
    """Calculated metrics for journals"""
    __tablename__ = 'journal_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, nullable=False, index=True)
    
    # Website quality metrics
    technical_score = Column(Float)  # 0-100
    design_score = Column(Float)     # 0-100
    content_score = Column(Float)    # 0-100
    contact_score = Column(Float)    # 0-100
    
    # Editorial quality metrics
    board_quality_score = Column(Float)    # 0-100
    review_process_score = Column(Float)   # 0-100
    ethics_score = Column(Float)           # 0-100
    
    # Publication metrics
    publication_pattern_score = Column(Float)  # 0-100
    citation_integrity_score = Column(Float)   # 0-100
    indexing_score = Column(Float)             # 0-100
    
    # Final scores
    overall_score = Column(Float)      # 0-100
    predatory_probability = Column(Float)  # 0-1
    
    # Feature importance
    feature_weights = Column(JSON)
    
    calculated_at = Column(DateTime, default=func.now())

class PredatoryIndicators(Base):
    """Specific predatory indicators found"""
    __tablename__ = 'predatory_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, nullable=False, index=True)
    
    indicator_type = Column(String(100), nullable=False)  # e.g., 'fake_impact_factor'
    indicator_description = Column(Text)
    severity = Column(String(20))  # 'low', 'medium', 'high', 'critical'
    evidence = Column(JSON)  # Store supporting evidence
    
    detected_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

class ScrapingLog(Base):
    """Log of scraping activities"""
    __tablename__ = 'scraping_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, index=True)
    url = Column(String(1000), nullable=False)
    
    # Scraping details
    scrape_type = Column(String(100))  # 'full', 'update', 'verify'
    success = Column(Boolean)
    error_message = Column(Text)
    response_time = Column(Float)
    
    # Data collected
    pages_scraped = Column(Integer, default=0)
    data_size = Column(Integer)  # Size in bytes
    
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

class ModelPerformance(Base):
    """Track model performance over time"""
    __tablename__ = 'model_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=False)  # 'random_forest', 'xgboost', etc.
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Dataset info
    training_size = Column(Integer)
    test_size = Column(Integer)
    cross_val_score = Column(Float)
    
    # Feature importance
    top_features = Column(JSON)
    feature_importance = Column(JSON)
    
    # Model metadata
    hyperparameters = Column(JSON)
    training_time = Column(Float)  # seconds
    
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=False)  # Current production model

class UserFeedback(Base):
    """User feedback on journal assessments"""
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(Integer, nullable=False, index=True)
    
    # User information (optional)
    user_email = Column(String(300))
    user_institution = Column(String(500))
    
    # Feedback details
    feedback_type = Column(String(50))  # 'correction', 'confirmation', 'dispute'
    user_assessment = Column(String(50))  # 'legitimate', 'predatory', 'unsure'
    comments = Column(Text)
    evidence_urls = Column(JSON)
    
    # System response
    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)
    action_taken = Column(String(200))
    
    submitted_at = Column(DateTime, default=func.now())
    reviewed_at = Column(DateTime)

