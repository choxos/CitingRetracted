#!/usr/bin/env python3
"""
Configuration settings for Predatory Journal Detector
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.absolute()
    DATA_DIR = PROJECT_ROOT / "data"
    MODELS_DIR = PROJECT_ROOT / "models"
    LOGS_DIR = PROJECT_ROOT / "logs"
    CACHE_DIR = PROJECT_ROOT / "cache"
    
    # Create directories if they don't exist
    for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
        directory.mkdir(exist_ok=True)
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/predatory_journals")
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/predatory_journals")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_KEY = os.getenv("API_KEY", "your-api-key-here")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Scraping Configuration
    SCRAPING_DELAY = float(os.getenv("SCRAPING_DELAY", 1.0))  # Delay between requests
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", 10))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    USER_AGENT = "PredatoryJournalDetector/1.0 (Research Tool)"
    
    # External APIs
    OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "your-email@example.com")
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    CROSSREF_MAILTO = os.getenv("CROSSREF_MAILTO", "your-email@example.com")
    
    # Machine Learning Configuration
    MODEL_RANDOM_STATE = 42
    CV_FOLDS = 10
    TEST_SIZE = 0.2
    N_ESTIMATORS = 100
    MAX_FEATURES = "sqrt"
    
    # Scoring Thresholds
    LEGITIMATE_THRESHOLD = 20
    MODERATE_RISK_THRESHOLD = 40
    HIGH_RISK_THRESHOLD = 60
    VERY_HIGH_RISK_THRESHOLD = 80
    
    # Feature Engineering
    MIN_EDITORIAL_BOARD_SIZE = 5
    MAX_REASONABLE_PUBLICATION_FEE = 3000  # USD
    MIN_PUBLICATION_HISTORY_YEARS = 1
    
    # Known Legitimate Publishers
    LEGITIMATE_PUBLISHERS = {
        "Elsevier", "Springer", "Wiley", "Taylor & Francis", "Sage",
        "Oxford University Press", "Cambridge University Press",
        "Nature Publishing Group", "Public Library of Science",
        "BioMed Central", "Frontiers Media", "MDPI", "Hindawi",
        "IEEE", "ACM", "ACS", "RSC", "IOP Publishing"
    }
    
    # Known Predatory Indicators
    PREDATORY_KEYWORDS = {
        "rapid publication", "fast track", "within days",
        "guaranteed acceptance", "nobel laureate editor",
        "impact factor will be", "fake impact factor",
        "pay after acceptance", "bitcoin payment"
    }
    
    # Country Risk Scores (based on known patterns)
    COUNTRY_RISK_SCORES = {
        "Nigeria": 0.8, "India": 0.6, "Pakistan": 0.7,
        "Bangladesh": 0.7, "Iran": 0.5, "Turkey": 0.4,
        "USA": 0.1, "UK": 0.1, "Germany": 0.1,
        "Canada": 0.1, "Australia": 0.1, "Netherlands": 0.1
    }
    
    # Web Scraping Selectors
    SELECTORS = {
        "title": ["title", "h1.title", ".journal-title", "#title"],
        "editorial_board": [".editorial-board", "#editors", ".board-members"],
        "submission_info": [".submission", "#submit", ".author-guidelines"],
        "contact_info": [".contact", "#contact", ".contact-info"],
        "fees_info": [".fees", "#publication-fees", ".charges", ".apc"]
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    
    # Cache Configuration
    CACHE_EXPIRE_HOURS = 24
    CACHE_MAX_SIZE = 1000
    
    # Model Performance Thresholds
    MIN_ACCURACY = 0.85
    MIN_PRECISION = 0.80
    MIN_RECALL = 0.80
    MIN_F1_SCORE = 0.80

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "WARNING"
    
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///test.db"
    LOG_LEVEL = "DEBUG"

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

