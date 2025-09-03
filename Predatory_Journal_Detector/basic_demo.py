#!/usr/bin/env python3
"""
Basic Demo for Predatory Journal Detector
Standalone demo that works with minimal dependencies
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os
import logging

def main():
    """Run the basic demo"""
    print("🎯 Predatory Journal Detector - BASIC DEMO")
    print("=" * 50)
    print("This is a basic demonstration of the core concept.")
    print("=" * 50)
    
    # Test basic Python functionality
    print("\n📊 SYSTEM CHECK:")
    print(f"✅ Python version: {sys.version.split()[0]}")
    print(f"✅ Working directory: {os.getcwd()}")
    print(f"✅ Platform: {sys.platform}")
    
    # Test basic web requests
    print("\n🌐 TESTING WEB ACCESS:")
    try:
        import requests
        print("✅ Requests library available")
        
        # Test simple web request
        test_url = "https://httpbin.org/json"
        print(f"🔍 Testing web access to: {test_url}")
        
        start_time = time.time()
        response = requests.get(test_url, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Web request successful!")
            print(f"   Status: {response.status_code}")
            print(f"   Response time: {response_time:.2f}s")
            print(f"   Content size: {len(response.content)} bytes")
            
            # Try to parse JSON
            try:
                data = response.json()
                print(f"   JSON data received: {len(data)} fields")
            except:
                print("   Text content received")
        else:
            print(f"⚠️  Request returned status: {response.status_code}")
            
    except ImportError:
        print("❌ Requests library not available")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"❌ Web request failed: {e}")
    
    # Test HTML parsing
    print("\n📝 TESTING HTML PARSING:")
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup library available")
        
        # Test HTML parsing
        test_html = """
        <html>
            <head><title>Test Journal</title></head>
            <body>
                <h1>International Journal of Test Sciences</h1>
                <div class="editorial-board">
                    <h2>Editorial Board</h2>
                    <p>Dr. John Smith, Editor-in-Chief</p>
                    <p>Prof. Jane Doe, Associate Editor</p>
                </div>
                <div class="contact">
                    <h2>Contact</h2>
                    <p>Email: editor@testjournal.com</p>
                    <p>Phone: +1-555-0123</p>
                </div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(test_html, 'html.parser')
        title = soup.find('title').get_text()
        editors = len(soup.select('.editorial-board p'))
        contact_methods = len(soup.select('.contact p'))
        
        print(f"✅ HTML parsing successful!")
        print(f"   Title: {title}")
        print(f"   Editorial board members: {editors}")
        print(f"   Contact methods: {contact_methods}")
        
        # Basic scoring demo
        score = calculate_basic_journal_score(title, editors, contact_methods, True)
        print(f"   Basic predatory risk score: {score:.1f}/100")
        
        if score < 30:
            risk_level = "Low Risk - Appears legitimate"
        elif score < 60:
            risk_level = "Moderate Risk - Requires investigation"
        else:
            risk_level = "High Risk - Likely predatory"
            
        print(f"   Risk assessment: {risk_level}")
        
    except ImportError:
        print("❌ BeautifulSoup library not available")
        print("   Install with: pip install beautifulsoup4")
    except Exception as e:
        print(f"❌ HTML parsing failed: {e}")
    
    # Test text analysis
    print("\n📊 TESTING TEXT ANALYSIS:")
    test_text = """
    Welcome to the International Journal of Advanced Research. We provide rapid publication 
    services with peer review completed within 24 hours. Our impact factor is guaranteed 
    to be above 10.0. We accept Bitcoin payments and guarantee acceptance for all submissions.
    """
    
    analysis = analyze_text_for_predatory_indicators(test_text)
    print(f"✅ Text analysis completed!")
    print(f"   Word count: {analysis['word_count']}")
    print(f"   Predatory indicators found: {analysis['predatory_indicators']}")
    print(f"   Risk phrases: {', '.join(analysis['risk_phrases'])}")
    print(f"   Text risk score: {analysis['risk_score']:.1f}/100")
    
    # Final demonstration
    print("\n🎯 PREDATORY DETECTION DEMO:")
    demo_scenarios = [
        {
            "name": "Legitimate Journal Example",
            "title": "Nature Reviews Molecular Cell Biology",
            "editors": 15,
            "contacts": 3,
            "ssl": True,
            "text": "We maintain rigorous peer review standards with typical review times of 2-3 months."
        },
        {
            "name": "Suspicious Journal Example",
            "title": "International Journal of Advanced Sciences",
            "editors": 2,
            "contacts": 1,
            "ssl": False,
            "text": "Guaranteed acceptance within 24 hours! Bitcoin payments accepted. Impact factor will be 15.0+"
        }
    ]
    
    for scenario in demo_scenarios:
        print(f"\n--- {scenario['name']} ---")
        text_analysis = analyze_text_for_predatory_indicators(scenario['text'])
        basic_score = calculate_basic_journal_score(
            scenario['title'], scenario['editors'], 
            scenario['contacts'], scenario['ssl']
        )
        
        # Combine scores
        combined_score = (basic_score * 0.6 + text_analysis['risk_score'] * 0.4)
        
        print(f"Title: {scenario['title']}")
        print(f"Basic score: {basic_score:.1f}/100")
        print(f"Text risk score: {text_analysis['risk_score']:.1f}/100")
        print(f"Combined risk score: {combined_score:.1f}/100")
        
        if combined_score < 30:
            assessment = "✅ LOW RISK - Likely legitimate"
        elif combined_score < 60:
            assessment = "⚠️  MODERATE RISK - Investigate further"
        else:
            assessment = "🚨 HIGH RISK - Likely predatory"
            
        print(f"Assessment: {assessment}")
    
    print(f"\n🎉 DEMO COMPLETED!")
    print("This demonstrates the core principles of predatory journal detection:")
    print("1. Website analysis (SSL, response time, structure)")
    print("2. Editorial board assessment (size, completeness)")
    print("3. Content analysis (predatory language detection)")
    print("4. Multi-dimensional scoring and risk assessment")
    print("\nFor the full system with ML models and advanced features:")
    print("- Install all dependencies: pip install -r requirements.txt")
    print("- Run: python demo.py")
    print("- Start API: python api/main.py")

def calculate_basic_journal_score(title, editors, contacts, has_ssl):
    """Calculate basic predatory risk score"""
    score = 0  # Start with 0 risk
    
    # Title analysis
    if "international" in title.lower() and "advanced" in title.lower():
        score += 15  # Generic suspicious titles
    
    # Editorial board size
    if editors < 3:
        score += 25  # Very small board
    elif editors < 10:
        score += 10  # Small board
    
    # Contact information
    if contacts < 2:
        score += 20  # Limited contact info
    
    # SSL certificate
    if not has_ssl:
        score += 15  # No SSL
    
    return min(score, 100)

def analyze_text_for_predatory_indicators(text):
    """Analyze text for predatory publishing indicators"""
    predatory_phrases = [
        "rapid publication", "within 24 hours", "guaranteed acceptance",
        "bitcoin", "cryptocurrency", "impact factor will be", "guaranteed impact",
        "fast track", "immediate publication", "pay after acceptance"
    ]
    
    words = text.lower().split()
    word_count = len(words)
    
    risk_phrases = []
    predatory_indicators = 0
    
    for phrase in predatory_phrases:
        if phrase in text.lower():
            risk_phrases.append(phrase)
            predatory_indicators += 1
    
    # Calculate risk score
    risk_score = min(predatory_indicators * 20, 100)  # 20 points per indicator
    
    return {
        'word_count': word_count,
        'predatory_indicators': predatory_indicators,
        'risk_phrases': risk_phrases,
        'risk_score': risk_score
    }

if __name__ == "__main__":
    main()

