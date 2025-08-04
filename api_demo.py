#!/usr/bin/env python3
"""
PRCT Democracy Analysis API Demo
Quick demonstration of the new API endpoints
"""

import requests
import json
from datetime import datetime

def demo_api(base_url="https://prct.xeradb.com"):
    """Demonstrate democracy analysis API endpoints"""
    
    print("🚀 PRCT Democracy Analysis API Demo")
    print(f"🌐 Base URL: {base_url}")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        {
            'name': 'Democracy Analysis Overview',
            'url': '/api/democracy/overview/',
            'description': 'Complete analysis data with all components'
        },
        {
            'name': 'Raw Data Explorer',
            'url': '/api/democracy/raw-data/?limit=5',
            'description': 'Variable statistics and sample data'
        },
        {
            'name': 'Visualization Data',
            'url': '/api/democracy/visualizations/?chart_type=democracy_retraction_scatter',
            'description': 'Chart data for scatter plot'
        },
        {
            'name': 'Model Diagnostics',
            'url': '/api/democracy/model-diagnostics/',
            'description': 'Bayesian model convergence and fit metrics'
        },
        {
            'name': 'Statistical Results',
            'url': '/api/democracy/statistical-results/',
            'description': 'Statistical analysis results from hierarchical model'
        },
        {
            'name': 'Methodology Information',
            'url': '/api/democracy/methodology/',
            'description': 'Methods, data sources, and key findings'
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n{i}. 📊 {endpoint['name']}")
        print(f"   📝 {endpoint['description']}")
        print(f"   🔗 {endpoint['url']}")
        
        try:
            start_time = datetime.now()
            response = requests.get(f"{base_url}{endpoint['url']}", timeout=10)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code} ({response_time:.0f}ms)")
                
                # Show some data structure info
                if 'data' in data:
                    data_keys = list(data['data'].keys()) if isinstance(data['data'], dict) else []
                    print(f"   📋 Data sections: {', '.join(data_keys[:5])}")
                    
                    if 'metadata' in data:
                        metadata = data['metadata']
                        print(f"   ℹ️  Endpoint: {metadata.get('endpoint', 'N/A')}")
                        print(f"   🕒 Generated: {metadata.get('generated_at', 'N/A')}")
                        
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Response: {response.text[:100]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 API Demo Complete!")
    print("\n📚 For full documentation, see: API_DOCUMENTATION.md")
    print("🧪 For comprehensive testing, run: python3 test_democracy_api.py")

if __name__ == '__main__':
    import sys
    
    # Allow specifying base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://prct.xeradb.com"
    
    demo_api(base_url)