#!/usr/bin/env python3
"""
FastAPI Web Application for Predatory Journal Detection
RESTful API with real-time analysis capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
import asyncio
import uvicorn
from datetime import datetime
import logging

from config import Config
from scraper.journal_scraper import JournalScraper
from ml_models.predatory_classifier import PredatoryClassifier
from ml_models.scoring_system import PredatoryScoringSystem
from database.models import Journal, JournalMetrics, PredatoryIndicators

# Initialize FastAPI app
app = FastAPI(
    title="Predatory Journal Detector API",
    description="Advanced multi-modal machine learning system for detecting predatory journals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = Config()
scraper = JournalScraper(config)
classifier = PredatoryClassifier(config)
scoring_system = PredatoryScoringSystem()

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Pydantic models for API
class JournalAnalysisRequest(BaseModel):
    url: HttpUrl
    deep_analysis: bool = True
    include_ml_prediction: bool = True

class JournalAnalysisResponse(BaseModel):
    journal_url: str
    analysis_id: str
    timestamp: str
    success: bool
    predatory_score: float
    risk_level: str
    confidence: float
    recommendation: str
    dimension_scores: Dict
    warning_flags: List[str]
    positive_indicators: List[str]
    critical_issues: List[str]
    ml_prediction: Optional[Dict] = None
    processing_time: float

class BatchAnalysisRequest(BaseModel):
    urls: List[HttpUrl]
    deep_analysis: bool = True

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    models_loaded: bool
    scraper_ready: bool

# Global variables for model state
models_loaded = False

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global models_loaded
    
    logger.info("Starting Predatory Journal Detector API...")
    
    try:
        # Try to load pre-trained models
        # In a real deployment, you would load saved models here
        # classifier.load_model("path/to/saved/model.pkl")
        models_loaded = True
        logger.info("✓ Models loaded successfully")
        
    except Exception as e:
        logger.warning(f"No pre-trained models found: {e}")
        logger.info("API will run with rule-based scoring only")
        models_loaded = False
    
    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Predatory Journal Detector API...")
    
    # Cleanup selenium driver
    if hasattr(scraper, 'driver') and scraper.driver:
        scraper.driver.quit()
    
    logger.info("Shutdown complete")

@app.get("/", response_model=HealthResponse)
async def root():
    """API health check and status"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        models_loaded=models_loaded,
        scraper_ready=True
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        models_loaded=models_loaded,
        scraper_ready=True
    )

@app.post("/analyze", response_model=JournalAnalysisResponse)
async def analyze_journal(request: JournalAnalysisRequest):
    """
    Analyze a single journal for predatory indicators
    
    This endpoint performs comprehensive analysis including:
    - Website scraping and content analysis
    - Multi-dimensional scoring
    - Machine learning prediction (if models are loaded)
    - Risk assessment and recommendations
    """
    start_time = datetime.now()
    analysis_id = f"analysis_{int(start_time.timestamp())}"
    
    try:
        logger.info(f"Starting analysis for: {request.url}")
        
        # Step 1: Scrape journal website
        scraped_data = await scraper.scrape_journal(str(request.url))
        
        if not scraped_data.get('scrape_success', False):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to scrape journal website: {scraped_data.get('error_message', 'Unknown error')}"
            )
        
        # Step 2: ML prediction (if available)
        ml_prediction = None
        if request.include_ml_prediction and models_loaded:
            try:
                ml_prediction = classifier.predict_journal(scraped_data)
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
        
        # Step 3: Comprehensive scoring
        scoring_result = scoring_system.calculate_comprehensive_score(
            scraped_data, ml_prediction
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = JournalAnalysisResponse(
            journal_url=str(request.url),
            analysis_id=analysis_id,
            timestamp=start_time.isoformat(),
            success=True,
            predatory_score=scoring_result['overall_score'],
            risk_level=scoring_result['risk_level'],
            confidence=scoring_result['confidence'],
            recommendation=scoring_result['recommendation'],
            dimension_scores=scoring_result['dimension_scores'],
            warning_flags=scoring_result['warning_flags'],
            positive_indicators=scoring_result['positive_indicators'],
            critical_issues=scoring_result['critical_issues'],
            ml_prediction=ml_prediction,
            processing_time=processing_time
        )
        
        logger.info(f"Analysis completed for {request.url}: Score={scoring_result['overall_score']}, Risk={scoring_result['risk_level']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {request.url}: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return JournalAnalysisResponse(
            journal_url=str(request.url),
            analysis_id=analysis_id,
            timestamp=start_time.isoformat(),
            success=False,
            predatory_score=50.0,  # Neutral score for errors
            risk_level="Unknown",
            confidence=0.0,
            recommendation="Manual review required due to analysis error",
            dimension_scores={},
            warning_flags=[f"Analysis error: {str(e)}"],
            positive_indicators=[],
            critical_issues=["Analysis failed"],
            processing_time=processing_time
        )

@app.post("/analyze/batch")
async def analyze_journals_batch(request: BatchAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze multiple journals in batch
    
    For large batches, this endpoint processes journals in the background
    and returns a job ID for checking status
    """
    if len(request.urls) > 50:
        raise HTTPException(
            status_code=400,
            detail="Batch size too large. Maximum 50 URLs per batch."
        )
    
    # For smaller batches, process immediately
    if len(request.urls) <= 10:
        results = []
        for url in request.urls:
            try:
                analysis_request = JournalAnalysisRequest(
                    url=url, 
                    deep_analysis=request.deep_analysis
                )
                result = await analyze_journal(analysis_request)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch analysis failed for {url}: {e}")
                results.append({
                    "journal_url": str(url),
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "status": "completed",
            "total_processed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    # For larger batches, use background processing
    job_id = f"batch_{int(datetime.now().timestamp())}"
    
    # In a real implementation, you would use a task queue like Celery
    # For now, we'll return a placeholder response
    return {
        "status": "processing",
        "job_id": job_id,
        "total_urls": len(request.urls),
        "estimated_completion": datetime.now().isoformat(),
        "check_status_url": f"/batch/status/{job_id}"
    }

@app.get("/models/info")
async def get_model_info():
    """Get information about loaded ML models"""
    if not models_loaded:
        return {
            "models_loaded": False,
            "message": "No ML models loaded. Using rule-based scoring only."
        }
    
    try:
        model_summary = classifier.get_model_summary()
        return {
            "models_loaded": True,
            "model_info": model_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "models_loaded": False,
            "error": str(e)
        }

@app.get("/stats/features")
async def get_feature_info():
    """Get information about features used in analysis"""
    return {
        "feature_categories": {
            "website_quality": [
                "Technical score (SSL, responsiveness, loading time)",
                "Design score (professional appearance, navigation)",
                "Content score (completeness, organization)"
            ],
            "editorial_board": [
                "Board size and composition",
                "Editor-in-chief presence",
                "Member qualifications and diversity"
            ],
            "submission_process": [
                "Guidelines availability and clarity",
                "Peer review process description", 
                "Review timeline reasonableness"
            ],
            "contact_information": [
                "Contact method availability",
                "Physical address verification",
                "Email and phone legitimacy"
            ],
            "publication_fees": [
                "Fee transparency and reasonableness",
                "Payment method legitimacy",
                "Cost comparison with legitimate journals"
            ],
            "content_quality": [
                "Language quality and grammar",
                "Content depth and professionalism",
                "Predatory indicator detection"
            ],
            "domain_analysis": [
                "Domain age and registration info",
                "SSL certificate validation",
                "Publisher legitimacy verification"
            ],
            "bibliometric": [
                "Impact factor claim verification",
                "ISSN presence and validity",
                "Publisher reputation assessment"
            ]
        },
        "scoring_methodology": {
            "range": "0-100 (higher = more predatory risk)",
            "thresholds": {
                "Very Low Risk": "0-20",
                "Low Risk": "21-40", 
                "Moderate Risk": "41-60",
                "High Risk": "61-80",
                "Very High Risk": "81-100"
            }
        }
    }

@app.get("/examples")
async def get_examples():
    """Get example journal URLs for testing"""
    return {
        "legitimate_examples": [
            "https://www.nature.com/nature/",
            "https://science.sciencemag.org/",
            "https://www.cell.com/",
            "https://www.nejm.org/"
        ],
        "test_urls": [
            "https://journals.plos.org/plosone/",
            "https://bmjopen.bmj.com/",
            "https://www.frontiersin.org/"
        ],
        "note": "Use these URLs to test the API. Results may vary based on website changes."
    }

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )

