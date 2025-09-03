#!/usr/bin/env python3
"""
Demonstration Script for Predatory Journal Detector
Shows system capabilities with example analyses
"""

import asyncio
import json
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from main import PredatoryJournalDetector

class Demo:
    """Demonstration class showcasing the system's capabilities"""
    
    def __init__(self):
        print("🎯 Predatory Journal Detector - DEMONSTRATION")
        print("=" * 60)
        print("This demo showcases the system's ability to analyze journals")
        print("and detect predatory publishing indicators.")
        print("=" * 60)
        
        self.detector = PredatoryJournalDetector()
        
        # Example URLs for demonstration
        self.example_journals = {
            "legitimate": [
                {
                    "name": "Nature",
                    "url": "https://www.nature.com/nature/",
                    "expected": "Very Low Risk",
                    "notes": "World's leading multidisciplinary science journal"
                },
                {
                    "name": "PLoS ONE",
                    "url": "https://journals.plos.org/plosone/",
                    "expected": "Low Risk",
                    "notes": "Open access journal with rigorous peer review"
                }
            ],
            "test_cases": [
                {
                    "name": "BMJ Open",
                    "url": "https://bmjopen.bmj.com/",
                    "expected": "Low Risk",
                    "notes": "Open access journal from BMJ publishing group"
                },
                {
                    "name": "Frontiers",
                    "url": "https://www.frontiersin.org/",
                    "expected": "Low-Moderate Risk",
                    "notes": "Legitimate but sometimes controversial open access publisher"
                }
            ]
        }
    
    async def run_full_demo(self):
        """Run complete demonstration"""
        print("\n🚀 Starting Full Demonstration...")
        
        # Demo 1: Single journal analysis
        await self.demo_single_analysis()
        
        # Demo 2: Batch analysis
        await self.demo_batch_analysis()
        
        # Demo 3: Feature extraction demonstration
        await self.demo_feature_extraction()
        
        # Demo 4: Scoring system explanation
        self.demo_scoring_explanation()
        
        # Demo 5: API usage examples
        self.demo_api_usage()
        
        print("\n✅ Demonstration completed successfully!")
        print("Check the output files for detailed results.")
    
    async def demo_single_analysis(self):
        """Demonstrate single journal analysis"""
        print("\n" + "="*60)
        print("1️⃣  SINGLE JOURNAL ANALYSIS DEMO")
        print("="*60)
        
        # Analyze Nature journal as example
        journal = self.example_journals["legitimate"][0]
        
        print(f"Analyzing: {journal['name']} ({journal['url']})")
        print(f"Expected Result: {journal['expected']}")
        print(f"Notes: {journal['notes']}")
        
        try:
            result = await self.detector.analyze_single_journal(
                journal["url"], 
                "demo_single_analysis.json"
            )
            
            # Additional insights
            if 'error' not in result:
                print(f"\n📊 ANALYSIS INSIGHTS:")
                print(f"   Processing time: {result.get('scrape_duration', 0):.2f} seconds")
                print(f"   Features extracted: {len(result.get('features', {}))}")
                print(f"   Dimensions analyzed: {len(result.get('dimension_scores', {}))}")
                
        except Exception as e:
            print(f"❌ Demo analysis failed: {e}")
            print("This may be due to network issues or website accessibility.")
    
    async def demo_batch_analysis(self):
        """Demonstrate batch analysis capabilities"""
        print("\n" + "="*60)
        print("2️⃣  BATCH ANALYSIS DEMO")
        print("="*60)
        
        # Collect all demo URLs
        all_journals = (self.example_journals["legitimate"] + 
                       self.example_journals["test_cases"])
        
        urls = [journal["url"] for journal in all_journals]
        
        print(f"Analyzing {len(urls)} journals in batch mode:")
        for i, journal in enumerate(all_journals, 1):
            print(f"  {i}. {journal['name']} - Expected: {journal['expected']}")
        
        try:
            results = await self.detector.analyze_multiple_journals(
                urls, 
                "demo_batch_analysis.json"
            )
            
            # Create comparative analysis
            self._create_comparison_report(results, all_journals)
            
        except Exception as e:
            print(f"❌ Batch demo failed: {e}")
    
    async def demo_feature_extraction(self):
        """Demonstrate feature extraction process"""
        print("\n" + "="*60)
        print("3️⃣  FEATURE EXTRACTION DEMO")
        print("="*60)
        
        print("This demo shows how we extract features from journal websites...")
        
        # Use a simpler URL for feature demo
        demo_url = self.example_journals["legitimate"][1]["url"]  # PLoS ONE
        
        print(f"Extracting features from: {demo_url}")
        
        try:
            # Scrape the journal
            scraped_data = await self.detector.scraper.scrape_journal(demo_url)
            
            if scraped_data.get('scrape_success'):
                # Extract features
                features = self.detector.feature_extractor.extract_features(scraped_data)
                
                print(f"\n📈 FEATURE EXTRACTION RESULTS:")
                print(f"   Total features extracted: {len(features)}")
                
                # Show feature categories
                feature_categories = {
                    'website_quality': ['technical_score', 'design_score', 'content_score'],
                    'editorial_board': ['board_size', 'board_quality_score', 'has_editor_in_chief'],
                    'submission_process': ['has_guidelines', 'peer_review_mentioned', 'timeline_mentioned'],
                    'contact_information': ['has_email', 'has_phone', 'has_address'],
                    'publication_fees': ['has_fees', 'fees_amount', 'suspicious_payment'],
                    'content_quality': ['word_count', 'readability_score', 'is_english'],
                    'domain_analysis': ['domain_age_days', 'domain_risk_score', 'ssl_valid'],
                    'bibliometric': ['claimed_impact_factor', 'issn_count', 'has_publisher_info']
                }
                
                print(f"\n📊 SAMPLE FEATURES BY CATEGORY:")
                for category, sample_features in feature_categories.items():
                    print(f"\n{category.replace('_', ' ').title()}:")
                    for feature in sample_features:
                        value = features.get(feature, 'N/A')
                        print(f"  {feature}: {value}")
                
                # Save detailed features
                with open("demo_features.json", "w") as f:
                    json.dump({
                        'url': demo_url,
                        'extraction_timestamp': datetime.now().isoformat(),
                        'features': features,
                        'feature_count': len(features),
                        'scraped_data_summary': {
                            'scrape_success': scraped_data.get('scrape_success'),
                            'scrape_duration': scraped_data.get('scrape_duration'),
                            'metadata': scraped_data.get('metadata', {})
                        }
                    }, f, indent=2)
                
                print(f"\n💾 Detailed features saved to demo_features.json")
            else:
                print(f"❌ Failed to scrape journal for feature demo")
                
        except Exception as e:
            print(f"❌ Feature extraction demo failed: {e}")
    
    def demo_scoring_explanation(self):
        """Explain the scoring system"""
        print("\n" + "="*60)
        print("4️⃣  SCORING SYSTEM EXPLANATION")
        print("="*60)
        
        print("""
🎯 SCORING METHODOLOGY:

The Predatory Journal Detector uses a multi-dimensional scoring approach:

📊 DIMENSION WEIGHTS:
   • Editorial Board (20%): Board size, member qualifications, diversity
   • Website Quality (15%): Technical quality, design, responsiveness  
   • Submission Process (15%): Guidelines clarity, peer review mention
   • Publication Fees (15%): Fee reasonableness, payment methods
   • Content Quality (10%): Language quality, predatory indicators
   • Contact Information (10%): Completeness, legitimacy
   • Domain Analysis (10%): Age, SSL certificates, registrar info
   • Bibliometric (5%): Impact factor claims, ISSN validation

🚦 RISK LEVELS:
   • Very Low Risk (0-20): Legitimate journals with strong indicators
   • Low Risk (21-40): Appears legitimate, minor concerns
   • Moderate Risk (41-60): Mixed signals, requires investigation  
   • High Risk (61-80): Multiple red flags, likely predatory
   • Very High Risk (81-100): Clear predatory indicators

⚖️  SCORING PROCESS:
   1. Individual dimension scoring (0-100 scale)
   2. Weighted combination of dimension scores
   3. Critical issue penalties (automatic risk increases)
   4. ML model integration (when available)
   5. Confidence calculation based on indicator consistency

🔍 KEY FEATURES:
   • Interpretable results with detailed explanations
   • Feature importance rankings
   • Uncertainty quantification
   • Actionable recommendations
        """)
    
    def demo_api_usage(self):
        """Show API usage examples"""
        print("\n" + "="*60)
        print("5️⃣  API USAGE EXAMPLES")
        print("="*60)
        
        print("""
🌐 STARTING THE API SERVER:
   python api/main.py
   # Server runs on http://localhost:8000

📡 API ENDPOINTS:

1. Single Journal Analysis:
   POST /analyze
   {
     "url": "https://example-journal.com",
     "deep_analysis": true,
     "include_ml_prediction": true
   }

2. Batch Analysis:
   POST /analyze/batch  
   {
     "urls": ["https://journal1.com", "https://journal2.com"],
     "deep_analysis": true
   }

3. Model Information:
   GET /models/info

4. Feature Information:
   GET /stats/features

5. Health Check:
   GET /health

🐍 PYTHON CLIENT EXAMPLE:
   
   import requests
   
   # Analyze single journal
   response = requests.post(
       "http://localhost:8000/analyze",
       json={"url": "https://example-journal.com"}
   )
   
   result = response.json()
   print(f"Risk Level: {result['risk_level']}")
   print(f"Score: {result['predatory_score']}")

🔧 CURL EXAMPLE:
   
   curl -X POST "http://localhost:8000/analyze" \\
        -H "Content-Type: application/json" \\
        -d '{"url": "https://example-journal.com"}'

📚 INTERACTIVE DOCS:
   Visit http://localhost:8000/docs for interactive API documentation
        """)
    
    def _create_comparison_report(self, results: list, journals_info: list):
        """Create a comparison report for batch results"""
        comparison_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_journals': len(results),
            'comparison_results': []
        }
        
        for i, (result, journal_info) in enumerate(zip(results, journals_info)):
            if 'error' not in result:
                comparison = {
                    'journal_name': journal_info['name'],
                    'url': journal_info['url'],
                    'expected_risk': journal_info['expected'],
                    'actual_score': result['predatory_score'],
                    'actual_risk': result['risk_level'],
                    'confidence': result['confidence'],
                    'match_expectation': self._assess_expectation_match(
                        journal_info['expected'], result['risk_level']
                    ),
                    'top_warnings': result['warning_flags'][:3],
                    'top_positives': result['positive_indicators'][:3]
                }
            else:
                comparison = {
                    'journal_name': journal_info['name'],
                    'url': journal_info['url'],
                    'expected_risk': journal_info['expected'],
                    'error': result['error']
                }
            
            comparison_data['comparison_results'].append(comparison)
        
        # Save comparison report
        with open("demo_comparison_report.json", "w") as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"\n📊 COMPARISON REPORT:")
        print(f"   Results saved to demo_comparison_report.json")
        
        # Print summary
        successful = [r for r in comparison_data['comparison_results'] if 'error' not in r]
        if successful:
            matches = sum(1 for r in successful if r.get('match_expectation', False))
            print(f"   Successful analyses: {len(successful)}/{len(results)}")
            print(f"   Expectation matches: {matches}/{len(successful)}")
    
    def _assess_expectation_match(self, expected: str, actual: str) -> bool:
        """Assess if actual result matches expectation"""
        expected_lower = expected.lower()
        actual_lower = actual.lower()
        
        # Simple matching logic
        if 'very low' in expected_lower and 'very low' in actual_lower:
            return True
        elif 'low' in expected_lower and ('low' in actual_lower or 'very low' in actual_lower):
            return True
        elif 'moderate' in expected_lower and 'moderate' in actual_lower:
            return True
        elif 'high' in expected_lower and ('high' in actual_lower or 'very high' in actual_lower):
            return True
        
        return False

async def main():
    """Run the demonstration"""
    demo = Demo()
    
    print("\n🎬 Choose demo mode:")
    print("1. Full demonstration (all features)")
    print("2. Quick demo (single analysis only)")
    print("3. Feature extraction demo")
    print("4. Scoring explanation only")
    
    try:
        choice = input("\nEnter choice (1-4, or press Enter for full demo): ").strip()
        
        if choice == "2":
            await demo.demo_single_analysis()
        elif choice == "3":
            await demo.demo_feature_extraction()
        elif choice == "4":
            demo.demo_scoring_explanation()
        else:
            await demo.run_full_demo()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

