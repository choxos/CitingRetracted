#!/usr/bin/env python3
"""
Main Application Entry Point
Predatory Journal Detector - Command Line Interface and Demonstration
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from scraper.journal_scraper import JournalScraper
from ml_models.predatory_classifier import PredatoryClassifier
from ml_models.scoring_system import PredatoryScoringSystem
from ml_models.feature_extractor import FeatureExtractor

class PredatoryJournalDetector:
    """Main application class for predatory journal detection"""
    
    def __init__(self, config_name: str = 'default'):
        self.config = Config()
        self.scraper = JournalScraper(self.config)
        self.classifier = PredatoryClassifier(self.config)
        self.scoring_system = PredatoryScoringSystem()
        self.feature_extractor = FeatureExtractor()
        
        print("🔍 Predatory Journal Detector Initialized")
        print(f"📊 Configuration: {config_name}")
        print("=" * 60)
    
    async def analyze_single_journal(self, url: str, output_file: str = None) -> Dict:
        """
        Analyze a single journal and return comprehensive results
        
        Args:
            url: Journal website URL
            output_file: Optional path to save results
            
        Returns:
            Dictionary containing analysis results
        """
        print(f"\n🌐 Analyzing Journal: {url}")
        print("-" * 40)
        
        try:
            # Step 1: Scrape journal data
            print("1️⃣  Scraping journal website...")
            scraped_data = await self.scraper.scrape_journal(url)
            
            if not scraped_data.get('scrape_success', False):
                print(f"❌ Scraping failed: {scraped_data.get('error_message', 'Unknown error')}")
                return {'error': 'Scraping failed', 'url': url}
            
            print(f"✅ Successfully scraped journal data")
            
            # Step 2: Extract features
            print("2️⃣  Extracting features...")
            features = self.feature_extractor.extract_features(scraped_data)
            print(f"✅ Extracted {len(features)} features")
            
            # Step 3: Calculate comprehensive score
            print("3️⃣  Calculating risk score...")
            scoring_result = self.scoring_system.calculate_comprehensive_score(scraped_data)
            
            # Step 4: ML prediction (if trained models available)
            ml_prediction = None
            try:
                print("4️⃣  Running ML prediction...")
                ml_prediction = self.classifier.predict_journal(scraped_data)
                print("✅ ML prediction completed")
            except Exception as e:
                print(f"⚠️  ML prediction unavailable: {e}")
            
            # Compile results
            result = {
                'analysis_timestamp': datetime.now().isoformat(),
                'journal_url': url,
                'scrape_duration': scraped_data.get('scrape_duration', 0),
                'predatory_score': scoring_result['overall_score'],
                'risk_level': scoring_result['risk_level'],
                'confidence': scoring_result['confidence'],
                'recommendation': scoring_result['recommendation'],
                'dimension_scores': scoring_result['dimension_scores'],
                'warning_flags': scoring_result['warning_flags'],
                'positive_indicators': scoring_result['positive_indicators'],
                'critical_issues': scoring_result['critical_issues'],
                'detailed_analysis': scoring_result['detailed_analysis'],
                'ml_prediction': ml_prediction,
                'scraped_metadata': scraped_data.get('metadata', {}),
                'features': features
            }
            
            # Display results
            self._display_analysis_results(result)
            
            # Save results if requested
            if output_file:
                self._save_results(result, output_file)
                print(f"💾 Results saved to {output_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {'error': str(e), 'url': url}
    
    async def analyze_multiple_journals(self, urls: List[str], output_file: str = None) -> List[Dict]:
        """
        Analyze multiple journals and return batch results
        
        Args:
            urls: List of journal URLs
            output_file: Optional path to save results
            
        Returns:
            List of analysis result dictionaries
        """
        print(f"\n📊 Batch Analysis: {len(urls)} journals")
        print("=" * 60)
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            
            try:
                result = await self.analyze_single_journal(url)
                results.append(result)
                
                # Brief summary for batch mode
                if 'error' not in result:
                    score = result['predatory_score']
                    risk = result['risk_level']
                    print(f"📈 Score: {score:.1f}/100 | Risk: {risk}")
                else:
                    print(f"❌ Error: {result['error']}")
                
            except Exception as e:
                print(f"❌ Failed to analyze {url}: {e}")
                results.append({'error': str(e), 'url': url})
        
        # Generate batch summary
        self._display_batch_summary(results)
        
        # Save batch results
        if output_file:
            self._save_batch_results(results, output_file)
            print(f"💾 Batch results saved to {output_file}")
        
        return results
    
    def train_models(self, training_data_file: str, output_model_file: str = None):
        """
        Train ML models using provided training data
        
        Args:
            training_data_file: Path to training data (CSV or JSON)
            output_model_file: Path to save trained model
        """
        print(f"\n🤖 Training ML Models")
        print(f"📂 Training data: {training_data_file}")
        print("-" * 40)
        
        try:
            # Load training data
            if training_data_file.endswith('.csv'):
                df = pd.read_csv(training_data_file)
            else:
                with open(training_data_file, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            
            print(f"📊 Loaded {len(df)} training samples")
            
            # Prepare data (this is a simplified example)
            # In practice, you'd need scraped data for each journal
            # and corresponding labels (1=predatory, 0=legitimate)
            
            # For demonstration, assuming the CSV has 'scraped_data' and 'is_predatory' columns
            if 'scraped_data' in df.columns and 'is_predatory' in df.columns:
                scraped_data_list = df['scraped_data'].tolist()
                labels = df['is_predatory'].tolist()
                
                # Prepare training data
                X, y, feature_names = self.classifier.prepare_training_data(scraped_data_list, labels)
                
                # Train models
                print("🔄 Training models...")
                training_results = self.classifier.train_models(X, y, feature_names)
                
                print("✅ Training completed!")
                print(f"📈 Best model: {training_results.get('best_model', 'N/A')}")
                
                # Save model
                if output_model_file:
                    self.classifier.save_model(output_model_file)
                    print(f"💾 Model saved to {output_model_file}")
                
                return training_results
            else:
                print("❌ Training data format not recognized")
                print("Expected columns: 'scraped_data', 'is_predatory'")
                return None
                
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return None
    
    def _display_analysis_results(self, result: Dict):
        """Display formatted analysis results"""
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)
        
        # Main scores
        print(f"🎯 Predatory Score: {result['predatory_score']:.1f}/100")
        print(f"⚠️  Risk Level: {result['risk_level']}")
        print(f"🎲 Confidence: {result['confidence']:.1f}%")
        print(f"💡 Recommendation: {result['recommendation']}")
        
        # Dimension breakdown
        print(f"\n📈 DIMENSION SCORES:")
        print("-" * 30)
        for dimension, data in result['dimension_scores'].items():
            score = data['score']
            print(f"{dimension.replace('_', ' ').title():<25}: {score:>6.1f}/100")
        
        # Issues and positives
        if result['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(result['critical_issues'])}):")
            for issue in result['critical_issues'][:5]:  # Show top 5
                print(f"  ❌ {issue}")
        
        if result['warning_flags']:
            print(f"\n⚠️  WARNING FLAGS ({len(result['warning_flags'])}):")
            for warning in result['warning_flags'][:5]:  # Show top 5
                print(f"  ⚠️  {warning}")
        
        if result['positive_indicators']:
            print(f"\n✅ POSITIVE INDICATORS ({len(result['positive_indicators'])}):")
            for positive in result['positive_indicators'][:5]:  # Show top 5
                print(f"  ✅ {positive}")
        
        # ML Prediction
        if result.get('ml_prediction'):
            ml_pred = result['ml_prediction']
            print(f"\n🤖 ML PREDICTION:")
            print(f"  Score: {ml_pred.get('predatory_score', 'N/A'):.1f}/100")
            print(f"  Prediction: {ml_pred.get('ensemble_prediction', 'N/A')}")
    
    def _display_batch_summary(self, results: List[Dict]):
        """Display batch analysis summary"""
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print(f"\n📊 BATCH SUMMARY")
        print("-" * 30)
        print(f"Total Analyzed: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            scores = [r['predatory_score'] for r in successful]
            risk_counts = {}
            for r in successful:
                risk = r['risk_level']
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            print(f"\nScore Statistics:")
            print(f"  Average Score: {sum(scores)/len(scores):.1f}")
            print(f"  Highest Score: {max(scores):.1f}")
            print(f"  Lowest Score: {min(scores):.1f}")
            
            print(f"\nRisk Distribution:")
            for risk, count in risk_counts.items():
                print(f"  {risk}: {count}")
    
    def _save_results(self, result: Dict, output_file: str):
        """Save single analysis results"""
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def _save_batch_results(self, results: List[Dict], output_file: str):
        """Save batch analysis results"""
        batch_data = {
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': len(results),
            'results': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(batch_data, f, indent=2)

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Predatory Journal Detector")
    parser.add_argument('command', choices=['analyze', 'batch', 'train', 'demo'], 
                       help='Command to execute')
    parser.add_argument('--url', '-u', help='Journal URL to analyze')
    parser.add_argument('--file', '-f', help='File containing URLs or training data')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--model', '-m', help='Model file for training/loading')
    parser.add_argument('--config', '-c', default='default', help='Configuration profile')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = PredatoryJournalDetector(args.config)
    
    if args.command == 'analyze':
        if not args.url:
            print("❌ URL required for single analysis. Use --url parameter.")
            sys.exit(1)
        
        await detector.analyze_single_journal(args.url, args.output)
    
    elif args.command == 'batch':
        if not args.file:
            print("❌ Input file required for batch analysis. Use --file parameter.")
            sys.exit(1)
        
        # Read URLs from file
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        await detector.analyze_multiple_journals(urls, args.output)
    
    elif args.command == 'train':
        if not args.file:
            print("❌ Training data file required. Use --file parameter.")
            sys.exit(1)
        
        detector.train_models(args.file, args.model)
    
    elif args.command == 'demo':
        # Demonstration with example URLs
        print("🎯 DEMONSTRATION MODE")
        print("Analyzing example journals to show system capabilities...\n")
        
        demo_urls = [
            "https://www.nature.com/nature/",
            "https://journals.plos.org/plosone/"
        ]
        
        await detector.analyze_multiple_journals(demo_urls, args.output)

if __name__ == "__main__":
    asyncio.run(main())

