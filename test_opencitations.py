#!/usr/bin/env python3
"""
Test script for OpenCitations API integration
Run this to verify the API connection and data parsing works correctly.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')
django.setup()

from papers.management.commands.fetch_citations import OpenCitationsAPI, HybridCitationFetcher
from papers.models import RetractedPaper
import json

def test_opencitations_api():
    """Test basic OpenCitations API functionality"""
    print("🔗 Testing OpenCitations API Integration")
    print("=" * 50)
    
    # Initialize API
    oc_api = OpenCitationsAPI()
    
    # Test with a known DOI that should have citations
    test_doi = "10.1186/1756-8722-6-59"  # Example from documentation
    
    print(f"📄 Testing with DOI: {test_doi}")
    print()
    
    # Test citation count
    print("1️⃣ Testing citation count...")
    try:
        count = oc_api.get_citation_count(test_doi)
        print(f"   ✅ Citation count: {count}")
    except Exception as e:
        print(f"   ❌ Citation count failed: {e}")
    
    print()
    
    # Test getting citations
    print("2️⃣ Testing citation retrieval...")
    try:
        citations = oc_api.get_citations(test_doi)
        print(f"   ✅ Found {len(citations)} citations")
        
        if citations:
            print("   📋 Sample citation:")
            sample = citations[0]
            for key, value in sample.items():
                print(f"      {key}: {value}")
            
            # Test timespan parsing
            if 'timespan' in sample:
                timespan = sample['timespan']
                days = oc_api.parse_timespan(timespan)
                print(f"   ⏱️ Timespan '{timespan}' = {days} days")
                
    except Exception as e:
        print(f"   ❌ Citation retrieval failed: {e}")
    
    print()
    
    # Test metadata retrieval
    print("3️⃣ Testing metadata retrieval...")
    try:
        metadata = oc_api.get_metadata([test_doi])
        print(f"   ✅ Retrieved metadata for {len(metadata)} papers")
        
        if metadata:
            print("   📋 Sample metadata:")
            sample = metadata[0]
            for key, value in sample.items():
                if len(str(value)) > 100:
                    print(f"      {key}: {str(value)[:100]}...")
                else:
                    print(f"      {key}: {value}")
                    
    except Exception as e:
        print(f"   ❌ Metadata retrieval failed: {e}")
    
    print()

def test_hybrid_fetcher():
    """Test hybrid citation fetcher with a real retracted paper"""
    print("🔄 Testing Hybrid Citation Fetcher")
    print("=" * 50)
    
    # Find a retracted paper with a DOI
    paper = RetractedPaper.objects.filter(
        original_paper_doi__isnull=False,
        original_paper_doi__gt=''
    ).first()
    
    if not paper:
        print("❌ No retracted papers with DOIs found in database")
        return
    
    print(f"📄 Testing with paper: {paper.title[:60]}...")
    print(f"🔗 DOI: {paper.original_paper_doi}")
    print()
    
    # Initialize hybrid fetcher
    fetcher = HybridCitationFetcher()
    
    try:
        citations_found, citations_created = fetcher.fetch_citations_for_paper(paper)
        print(f"✅ Hybrid fetch completed:")
        print(f"   📊 Citations found: {citations_found}")
        print(f"   ✨ New citations created: {citations_created}")
        
        if citations_found > 0:
            print("   🎯 Successfully integrated with database!")
        else:
            print("   ℹ️ No citations found (may be expected for some papers)")
            
    except Exception as e:
        print(f"❌ Hybrid fetch failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test different OpenCitations API endpoints"""
    print("🌐 Testing API Endpoints")
    print("=" * 50)
    
    oc_api = OpenCitationsAPI()
    
    # Test different DOIs and endpoints
    test_cases = [
        {
            'doi': '10.1007/s11192-019-03217-6',
            'expected_citations': '>10',
            'description': 'Well-cited paper'
        },
        {
            'doi': '10.1002/adfm.201505328', 
            'expected_citations': '>5',
            'description': 'Technical paper'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}️⃣ Testing {case['description']}: {case['doi']}")
        
        try:
            # Test citation count endpoint
            count = oc_api.get_citation_count(case['doi'])
            print(f"   📊 Citation count: {count}")
            
            # Test citations endpoint (limit to first 5 for testing)
            citations = oc_api.get_citations(case['doi'])[:5]
            print(f"   📋 Sample citations: {len(citations)}")
            
            for citation in citations:
                citing_doi = citation.get('citing', 'N/A')
                creation = citation.get('creation', 'N/A')
                timespan = citation.get('timespan', 'N/A')
                print(f"      • {citing_doi} ({creation}, {timespan})")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print()

if __name__ == "__main__":
    print("🧪 OpenCitations Integration Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_opencitations_api()
        print()
        test_api_endpoints()
        print()
        test_hybrid_fetcher()
        print()
        
        print("🎉 Test suite completed!")
        print()
        print("💡 Next steps:")
        print("   1. Deploy to your VPS: git pull origin main")
        print("   2. Test with real data: python manage.py fetch_citations --source hybrid --limit 10")
        print("   3. Monitor logs for any issues")
        print("   4. Set up automated citation fetching with cron")
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 