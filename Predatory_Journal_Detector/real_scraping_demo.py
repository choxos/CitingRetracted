#!/usr/bin/env python3
"""
Real Web Scraping Demo for Predatory Journal Detector
Actually scrapes real journal websites and analyzes them
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import sys
from urllib.parse import urljoin, urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class RealJournalAnalyzer:
    """Actually scrapes and analyzes real journal websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_journal(self, url: str) -> dict:
        """Scrape a real journal website and extract key information"""
        print(f"\n🕷️  SCRAPING: {url}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Make request
            print("📡 Making HTTP request...")
            response = self.session.get(url, timeout=15)
            response_time = time.time() - start_time
            
            print(f"✅ Response received: {response.status_code} ({response_time:.2f}s)")
            print(f"📏 Content size: {len(response.content):,} bytes")
            
            if response.status_code != 200:
                print(f"⚠️  Non-200 status code: {response.status_code}")
                return {'error': f'HTTP {response.status_code}', 'url': url}
            
            # Parse HTML
            print("📝 Parsing HTML content...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            analysis = {
                'url': url,
                'scrape_timestamp': datetime.now().isoformat(),
                'response_time': response_time,
                'status_code': response.status_code,
                'page_size': len(response.content),
                'has_ssl': url.startswith('https://'),
                'final_url': response.url
            }
            
            # Extract title
            title_elem = soup.find('title')
            analysis['title'] = title_elem.get_text(strip=True) if title_elem else 'No title found'
            print(f"📰 Title: {analysis['title']}")
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            analysis['text_content'] = text_content
            analysis['word_count'] = len(text_content.split())
            print(f"📊 Word count: {analysis['word_count']:,}")
            
            # Analyze editorial board
            editorial_analysis = self.analyze_editorial_board(soup, text_content)
            analysis.update(editorial_analysis)
            
            # Analyze contact information
            contact_analysis = self.analyze_contact_info(soup, text_content)
            analysis.update(contact_analysis)
            
            # Analyze submission information
            submission_analysis = self.analyze_submission_info(text_content)
            analysis.update(submission_analysis)
            
            # Analyze predatory indicators
            predatory_analysis = self.analyze_predatory_indicators(text_content)
            analysis.update(predatory_analysis)
            
            # Calculate overall risk score
            risk_score = self.calculate_risk_score(analysis)
            analysis['risk_score'] = risk_score
            analysis['risk_level'] = self.get_risk_level(risk_score)
            
            return analysis
            
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
            return {'error': 'Timeout', 'url': url}
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")
            return {'error': 'Connection failed', 'url': url}
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {'error': str(e), 'url': url}
    
    def analyze_editorial_board(self, soup: BeautifulSoup, text: str) -> dict:
        """Analyze editorial board information"""
        print("👥 Analyzing editorial board...")
        
        # Look for editorial board sections
        board_indicators = ['editorial board', 'editors', 'editorial team', 'associate editors']
        board_text = ""
        
        # Try to find editorial sections
        for indicator in board_indicators:
            # Look for headings containing these terms
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                if indicator in heading.get_text().lower():
                    # Get the section after this heading
                    next_elements = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name and sibling.name.startswith('h'):
                            break  # Stop at next heading
                        next_elements.append(sibling.get_text())
                    board_text += ' '.join(next_elements)
        
        # Also check in full text for editor mentions
        editor_patterns = [
            r'editor[- ]in[- ]chief',
            r'associate editor',
            r'managing editor',
            r'editorial board',
            r'dr\.\s+\w+\s+\w+.*editor',
            r'prof\.\s+\w+\s+\w+.*editor'
        ]
        
        editor_mentions = 0
        for pattern in editor_patterns:
            matches = re.findall(pattern, text.lower())
            editor_mentions += len(matches)
        
        # Look for email patterns that might be editors
        editor_emails = re.findall(r'editor@\w+\.\w+|editorial@\w+\.\w+', text.lower())
        
        board_size_estimate = max(editor_mentions, len(editor_emails))
        
        analysis = {
            'editorial_board_mentions': editor_mentions,
            'editor_emails_found': len(editor_emails),
            'estimated_board_size': board_size_estimate,
            'has_editorial_info': board_size_estimate > 0
        }
        
        print(f"   Editor mentions: {editor_mentions}")
        print(f"   Editorial emails: {len(editor_emails)}")
        print(f"   Estimated board size: {board_size_estimate}")
        
        return analysis
    
    def analyze_contact_info(self, soup: BeautifulSoup, text: str) -> dict:
        """Analyze contact information"""
        print("📞 Analyzing contact information...")
        
        # Find emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        emails = list(set(emails))  # Remove duplicates
        
        # Find phone numbers
        phone_patterns = [
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s?\d{3}-?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        phones = list(set(phones))
        
        # Look for address information
        address_indicators = ['address', 'location', 'office', 'street', 'building', 'city', 'country']
        has_address_info = any(indicator in text.lower() for indicator in address_indicators)
        
        analysis = {
            'emails_found': emails,
            'email_count': len(emails),
            'phones_found': phones,
            'phone_count': len(phones),
            'has_address_info': has_address_info,
            'contact_methods_count': len(emails) + len(phones) + (1 if has_address_info else 0)
        }
        
        print(f"   Emails found: {len(emails)}")
        print(f"   Phones found: {len(phones)}")
        print(f"   Has address info: {has_address_info}")
        print(f"   Total contact methods: {analysis['contact_methods_count']}")
        
        return analysis
    
    def analyze_submission_info(self, text: str) -> dict:
        """Analyze submission guidelines and process"""
        print("📋 Analyzing submission information...")
        
        submission_keywords = [
            'submission guidelines', 'author guidelines', 'instructions for authors',
            'manuscript submission', 'submit manuscript', 'peer review'
        ]
        
        review_keywords = ['peer review', 'review process', 'reviewer', 'review time']
        
        timeline_patterns = [
            r'(\d+)\s*days?\s*(?:to|for)?\s*(?:review|decision)',
            r'(\d+)\s*weeks?\s*(?:to|for)?\s*(?:review|decision)',
            r'review\s*(?:process|time)[\s:]*(\d+)\s*(?:days?|weeks?)',
            r'within\s*(\d+)\s*(?:days?|weeks?|hours?)'
        ]
        
        has_submission_info = any(keyword in text.lower() for keyword in submission_keywords)
        has_review_info = any(keyword in text.lower() for keyword in review_keywords)
        
        # Extract timeline mentions
        timeline_mentions = []
        for pattern in timeline_patterns:
            matches = re.findall(pattern, text.lower())
            timeline_mentions.extend(matches)
        
        analysis = {
            'has_submission_guidelines': has_submission_info,
            'has_review_process_info': has_review_info,
            'timeline_mentions': timeline_mentions,
            'timeline_count': len(timeline_mentions)
        }
        
        print(f"   Has submission guidelines: {has_submission_info}")
        print(f"   Has review process info: {has_review_info}")
        print(f"   Timeline mentions: {len(timeline_mentions)}")
        
        return analysis
    
    def analyze_predatory_indicators(self, text: str) -> dict:
        """Analyze for predatory publishing indicators"""
        print("🚨 Analyzing predatory indicators...")
        
        # High-risk predatory indicators
        high_risk_patterns = [
            r'guaranteed?\s+acceptance',
            r'rapid\s+publication\s+within\s+\d+\s+(?:hours?|days?)',
            r'bitcoin|cryptocurrency\s+payment',
            r'impact\s+factor\s+will\s+be\s+\d+',
            r'fake\s+impact\s+factor',
            r'pay\s+(?:only\s+)?after\s+(?:acceptance|publication)',
            r'no\s+peer\s+review\s+required'
        ]
        
        # Medium-risk indicators
        medium_risk_patterns = [
            r'fast\s+track\s+publication',
            r'quick\s+publication',
            r'immediate\s+publication',
            r'within\s+24\s+hours',
            r'speedy\s+review'
        ]
        
        # Count occurrences
        high_risk_found = []
        medium_risk_found = []
        
        text_lower = text.lower()
        
        for pattern in high_risk_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                high_risk_found.extend(matches)
        
        for pattern in medium_risk_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                medium_risk_found.extend(matches)
        
        analysis = {
            'high_risk_indicators': high_risk_found,
            'medium_risk_indicators': medium_risk_found,
            'high_risk_count': len(high_risk_found),
            'medium_risk_count': len(medium_risk_found),
            'total_predatory_indicators': len(high_risk_found) + len(medium_risk_found)
        }
        
        print(f"   High-risk indicators: {len(high_risk_found)}")
        print(f"   Medium-risk indicators: {len(medium_risk_found)}")
        
        if high_risk_found:
            print(f"   🚨 High-risk flags: {high_risk_found[:3]}...")
        if medium_risk_found:
            print(f"   ⚠️  Medium-risk flags: {medium_risk_found[:3]}...")
        
        return analysis
    
    def calculate_risk_score(self, analysis: dict) -> float:
        """Calculate overall predatory risk score"""
        print("⚖️  Calculating risk score...")
        
        score = 0
        
        # Editorial board scoring (0-25 points)
        board_size = analysis.get('estimated_board_size', 0)
        if board_size == 0:
            score += 25  # No editorial board info
        elif board_size < 3:
            score += 20  # Very small board
        elif board_size < 5:
            score += 10  # Small board
        
        # Contact information scoring (0-20 points)
        contact_count = analysis.get('contact_methods_count', 0)
        if contact_count == 0:
            score += 20  # No contact info
        elif contact_count == 1:
            score += 15  # Very limited contact
        elif contact_count == 2:
            score += 5   # Limited contact
        
        # Technical scoring (0-15 points)
        if not analysis.get('has_ssl', False):
            score += 15  # No SSL
        
        if analysis.get('response_time', 0) > 5:
            score += 10  # Slow response
        
        # Content scoring (0-20 points)
        word_count = analysis.get('word_count', 0)
        if word_count < 100:
            score += 20  # Very little content
        elif word_count < 500:
            score += 10  # Limited content
        
        # Submission info scoring (0-20 points)
        if not analysis.get('has_submission_guidelines', False):
            score += 10
        if not analysis.get('has_review_process_info', False):
            score += 10
        
        # Predatory indicators (0-50 points) - most important
        high_risk = analysis.get('high_risk_count', 0)
        medium_risk = analysis.get('medium_risk_count', 0)
        
        score += high_risk * 25  # 25 points per high-risk indicator
        score += medium_risk * 10  # 10 points per medium-risk indicator
        
        return min(score, 100)
    
    def get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score < 20:
            return "Very Low Risk"
        elif score < 40:
            return "Low Risk"
        elif score < 60:
            return "Moderate Risk"
        elif score < 80:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def display_results(self, analysis: dict):
        """Display comprehensive analysis results"""
        if 'error' in analysis:
            print(f"\n❌ Analysis failed: {analysis['error']}")
            return
        
        print(f"\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE ANALYSIS RESULTS")
        print(f"=" * 80)
        print(f"🌐 URL: {analysis['url']}")
        print(f"📰 Title: {analysis['title']}")
        print(f"⏱️  Response Time: {analysis['response_time']:.2f}s")
        print(f"📏 Content Size: {analysis['page_size']:,} bytes")
        print(f"📝 Word Count: {analysis['word_count']:,}")
        print(f"🔒 SSL: {'Yes' if analysis['has_ssl'] else 'No'}")
        
        print(f"\n📊 RISK ASSESSMENT:")
        print(f"🎯 Overall Risk Score: {analysis['risk_score']:.1f}/100")
        print(f"⚠️  Risk Level: {analysis['risk_level']}")
        
        if analysis['risk_score'] < 30:
            recommendation = "✅ APPEARS LEGITIMATE - Low risk indicators"
        elif analysis['risk_score'] < 60:
            recommendation = "⚠️  INVESTIGATE FURTHER - Mixed signals"
        else:
            recommendation = "🚨 HIGH RISK - Multiple red flags detected"
        
        print(f"💡 Recommendation: {recommendation}")
        
        # Detailed breakdown
        print(f"\n📋 DETAILED BREAKDOWN:")
        print(f"👥 Editorial Board: {analysis.get('estimated_board_size', 0)} members estimated")
        print(f"📞 Contact Methods: {analysis.get('contact_methods_count', 0)} found")
        print(f"📋 Submission Info: {'Yes' if analysis.get('has_submission_guidelines') else 'No'}")
        print(f"🔍 Review Process: {'Yes' if analysis.get('has_review_process_info') else 'No'}")
        
        if analysis.get('total_predatory_indicators', 0) > 0:
            print(f"\n🚨 PREDATORY INDICATORS DETECTED:")
            if analysis.get('high_risk_count', 0) > 0:
                print(f"   ⚠️  High Risk: {analysis['high_risk_count']} indicators")
                for indicator in analysis.get('high_risk_indicators', [])[:3]:
                    print(f"      • {indicator}")
            if analysis.get('medium_risk_count', 0) > 0:
                print(f"   ⚠️  Medium Risk: {analysis['medium_risk_count']} indicators")
                for indicator in analysis.get('medium_risk_indicators', [])[:3]:
                    print(f"      • {indicator}")
        else:
            print(f"\n✅ No obvious predatory indicators detected")

def main():
    """Run real web scraping demo"""
    print("🎯 REAL WEB SCRAPING DEMO - Predatory Journal Detector")
    print("=" * 80)
    print("This demo will scrape actual journal websites and analyze them for")
    print("predatory indicators using real web data.")
    print("=" * 80)
    
    analyzer = RealJournalAnalyzer()
    
    # Test journals - mix of legitimate and potentially problematic
    test_journals = [
        {
            'name': 'PLOS ONE (Legitimate)',
            'url': 'https://journals.plos.org/plosone/',
            'expected': 'Low Risk'
        },
        {
            'name': 'BMJ Open (Legitimate)', 
            'url': 'https://bmjopen.bmj.com/',
            'expected': 'Low Risk'
        },
        {
            'name': 'Frontiers in Psychology (Legitimate but sometimes controversial)',
            'url': 'https://www.frontiersin.org/journals/psychology',
            'expected': 'Low-Moderate Risk'
        }
    ]
    
    results = []
    
    print(f"\n🚀 Starting analysis of {len(test_journals)} journals...")
    
    for i, journal in enumerate(test_journals, 1):
        print(f"\n" + "=" * 80)
        print(f"[{i}/{len(test_journals)}] ANALYZING: {journal['name']}")
        print(f"Expected: {journal['expected']}")
        print("=" * 80)
        
        try:
            result = analyzer.scrape_journal(journal['url'])
            result['name'] = journal['name']
            result['expected'] = journal['expected']
            results.append(result)
            
            analyzer.display_results(result)
            
            # Small delay to be respectful
            print("\n⏳ Waiting 3 seconds before next analysis...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Analysis interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            continue
    
    # Summary
    print(f"\n" + "=" * 80)
    print("📊 SUMMARY OF ALL ANALYSES")
    print("=" * 80)
    
    successful = [r for r in results if 'error' not in r]
    
    if successful:
        avg_score = sum(r['risk_score'] for r in successful) / len(successful)
        print(f"✅ Successfully analyzed: {len(successful)}/{len(test_journals)} journals")
        print(f"📊 Average risk score: {avg_score:.1f}/100")
        
        print(f"\n📋 RESULTS BREAKDOWN:")
        for result in successful:
            status = "✅" if result['risk_score'] < 40 else "⚠️" if result['risk_score'] < 70 else "🚨"
            print(f"   {status} {result['name']}: {result['risk_score']:.1f}/100 ({result['risk_level']})")
    
    print(f"\n🎉 Real web scraping demo completed!")
    print("This demonstrates the system actually analyzing live journal websites")
    print("with real data extraction and predatory indicator detection.")

if __name__ == "__main__":
    main()

