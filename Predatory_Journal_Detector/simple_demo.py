#!/usr/bin/env python3
"""
Simple Demo for Predatory Journal Detector
Basic functionality demonstration without heavy ML dependencies
"""

import asyncio
import json
from datetime import datetime
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from scraper.journal_scraper import JournalScraper
    from ml_models.scoring_system import PredatoryScoringSystem
    from config import Config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Some modules are missing. This is expected for the basic demo.")

class SimpleDemo:
    """Simple demonstration of basic functionality"""
    
    def __init__(self):
        print("🎯 Predatory Journal Detector - SIMPLE DEMO")
        print("=" * 50)
        print("This demo showcases basic web scraping and scoring")
        print("without requiring heavy ML dependencies.")
        print("=" * 50)
        
        # Setup basic logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        try:
            self.config = Config()
            self.scraper = JournalScraper(self.config)
            self.scoring_system = PredatoryScoringSystem()
            self.components_ready = True
        except Exception as e:
            print(f"⚠️  Some components not available: {e}")
            self.components_ready = False
    
    async def run_basic_demo(self):
        """Run basic demonstration"""
        print("\n🚀 Starting Basic Demonstration...")
        
        if not self.components_ready:
            print("❌ Core components not ready. Please check the setup.")
            return
        
        # Demo URLs (using reliable, accessible sites)
        demo_urls = [
            "https://httpbin.org/html",  # Simple test page
            "https://example.com",       # Basic example site
        ]
        
        for i, url in enumerate(demo_urls, 1):
            print(f"\n[{i}/{len(demo_urls)}] Analyzing: {url}")
            
            try:
                # Basic web scraping demo
                await self.demo_basic_scraping(url)
                
            except Exception as e:
                print(f"❌ Demo failed for {url}: {e}")
    
    async def demo_basic_scraping(self, url: str):
        """Demo basic web scraping functionality"""
        try:
            print(f"🕷️  Scraping website...")
            
            # Basic scraping (without selenium for simplicity)
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else "No title"
            
            text_content = soup.get_text(separator=' ', strip=True)
            word_count = len(text_content.split())
            
            # Basic analysis
            analysis = {
                'url': url,
                'title': title_text,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'page_size': len(response.content),
                'word_count': word_count,
                'has_ssl': url.startswith('https://'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Display results
            print(f"✅ Analysis completed!")
            print(f"   Title: {analysis['title'][:50]}...")
            print(f"   Status: {analysis['status_code']}")
            print(f"   Response time: {analysis['response_time']:.2f}s")
            print(f"   Page size: {analysis['page_size']:,} bytes")
            print(f"   Word count: {analysis['word_count']:,}")
            print(f"   SSL: {'Yes' if analysis['has_ssl'] else 'No'}")
            
            # Simple scoring demo
            score = self.calculate_basic_score(analysis)
            print(f"   Basic Quality Score: {score:.1f}/100")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return None
    
    def calculate_basic_score(self, analysis: dict) -> float:
        """Calculate a simple quality score"""
        score = 50  # Base score
        
        # SSL bonus
        if analysis.get('has_ssl', False):
            score += 20
        
        # Response time scoring
        response_time = analysis.get('response_time', 10)
        if response_time < 2:
            score += 15
        elif response_time < 5:
            score += 10
        
        # Content scoring
        word_count = analysis.get('word_count', 0)
        if word_count > 1000:
            score += 15
        elif word_count > 500:
            score += 10
        elif word_count > 100:
            score += 5
        
        # Status code
        if analysis.get('status_code') == 200:
            score += 10
        
        return min(score, 100)

async def main():
    """Run the simple demo"""
    demo = SimpleDemo()
    
    try:
        await demo.run_basic_demo()
        
        print("\n✅ Simple demo completed!")
        print("\nNext steps:")
        print("1. Install Chrome for advanced web scraping")
        print("2. Add optional packages: pip install shap matplotlib seaborn")
        print("3. Run the full demo: python demo.py")
        print("4. Start the API server: python api/main.py")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("This is normal for the basic demo setup.")

if __name__ == "__main__":
    asyncio.run(main())

