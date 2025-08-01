#!/usr/bin/env python3
"""
PRCT API Testing Suite
Comprehensive tests for all API endpoints
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from urllib.parse import urljoin

class PRCTAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "INFO":
            print(f"[{timestamp}] ℹ️  {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        elif level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "TEST":
            print(f"[{timestamp}] 🧪 {message}")
    
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with error handling"""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.Timeout:
            self.log(f"Request timeout for {endpoint}", "ERROR")
            return None
        except requests.exceptions.ConnectionError:
            self.log(f"Connection error for {endpoint}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Request failed for {endpoint}: {e}", "ERROR")
            return None
    
    def test_endpoint(self, name, method, endpoint, expected_status=200, **kwargs):
        """Generic endpoint test"""
        self.log(f"Testing {name}: {method} {endpoint}", "TEST")
        
        response = self.make_request(method, endpoint, **kwargs)
        
        if response is None:
            self.test_results.append({
                'name': name,
                'endpoint': endpoint,
                'status': 'FAILED',
                'error': 'No response received'
            })
            return None
        
        # Check status code
        if response.status_code != expected_status:
            self.log(f"Unexpected status code: {response.status_code} (expected {expected_status})", "ERROR")
            self.test_results.append({
                'name': name,
                'endpoint': endpoint,
                'status': 'FAILED',
                'error': f'Status code {response.status_code}'
            })
            return None
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.log(f"Invalid JSON response", "ERROR")
            self.test_results.append({
                'name': name,
                'endpoint': endpoint,
                'status': 'FAILED',
                'error': 'Invalid JSON response'
            })
            return None
        
        self.log(f"✅ {name} passed", "SUCCESS")
        self.test_results.append({
            'name': name,
            'endpoint': endpoint,
            'status': 'PASSED',
            'response_size': len(response.content),
            'response_time': response.elapsed.total_seconds()
        })
        
        return data
    
    def test_search_autocomplete(self):
        """Test search autocomplete endpoint"""
        # Test with valid query
        data = self.test_endpoint(
            "Search Autocomplete - Valid Query",
            "GET",
            "/api/search-autocomplete/?q=covid"
        )
        
        if data:
            assert 'suggestions' in data, "Response should contain 'suggestions'"
            self.log(f"Found {len(data['suggestions'])} suggestions", "INFO")
        
        # Test with short query (should return empty)
        data = self.test_endpoint(
            "Search Autocomplete - Short Query",
            "GET", 
            "/api/search-autocomplete/?q=co"
        )
        
        if data:
            assert data['suggestions'] == [], "Short query should return empty suggestions"
        
        # Test with empty query
        data = self.test_endpoint(
            "Search Autocomplete - Empty Query",
            "GET",
            "/api/search-autocomplete/"
        )
    
    def test_paper_citations(self):
        """Test paper citations endpoint"""
        # First, get a valid record_id from search
        search_data = self.make_request("GET", "/api/search-autocomplete/?q=science")
        
        if search_data and search_data.status_code == 200:
            suggestions = search_data.json().get('suggestions', [])
            if suggestions:
                record_id = suggestions[0]['record_id']
                self.log(f"Testing with record_id: {record_id}", "INFO")
                
                # Test with valid record_id
                data = self.test_endpoint(
                    "Paper Citations - Valid Record",
                    "GET",
                    f"/api/paper/{record_id}/citations/"
                )
                
                if data:
                    required_keys = [
                        'citations_by_year', 'post_retraction_by_year', 
                        'timeline_data', 'post_retraction_stats',
                        'total_citations', 'post_retraction_count'
                    ]
                    for key in required_keys:
                        assert key in data, f"Response should contain '{key}'"
        
        # Test with invalid record_id
        self.test_endpoint(
            "Paper Citations - Invalid Record",
            "GET",
            "/api/paper/INVALID123/citations/",
            expected_status=404
        )
    
    def test_post_retraction_analytics(self):
        """Test post-retraction analytics endpoint"""
        # Test basic request
        data = self.test_endpoint(
            "Post-Retraction Analytics - Basic",
            "GET",
            "/api/post-retraction-analytics/"
        )
        
        if data:
            required_keys = [
                'total_post_retraction', 'time_distribution', 
                'monthly_trend', 'filters_applied'
            ]
            for key in required_keys:
                assert key in data, f"Response should contain '{key}'"
        
        # Test with filters
        data = self.test_endpoint(
            "Post-Retraction Analytics - With Filters",
            "GET",
            "/api/post-retraction-analytics/?time_filter=1y&journal=nature&subject=medicine"
        )
        
        if data:
            filters = data.get('filters_applied', {})
            assert filters.get('time_filter') == '1y'
            assert filters.get('journal_filter') == 'nature'
            assert filters.get('subject_filter') == 'medicine'
    
    def test_analytics_data(self):
        """Test analytics data endpoint"""
        # Test different data types
        data_types = ['overview', 'trends', 'citations', 'subjects', 'geographic']
        
        for data_type in data_types:
            data = self.test_endpoint(
                f"Analytics Data - {data_type.title()}",
                "GET",
                f"/api/analytics-data/?type={data_type}"
            )
            
            if data:
                # Each type should return relevant data
                self.log(f"Analytics data type '{data_type}' returned {len(data)} keys", "INFO")
    
    def test_analytics_realtime(self):
        """Test real-time analytics endpoint"""
        data = self.test_endpoint(
            "Analytics Real-time",
            "GET",
            "/api/analytics-realtime/"
        )
        
        if data:
            required_keys = ['stats', 'recent_activity', 'citation_patterns', 'last_updated', 'status']
            for key in required_keys:
                assert key in data, f"Response should contain '{key}'"
            
            assert data['status'] == 'success', "Status should be 'success'"
    
    def test_optimized_analytics(self):
        """Test optimized analytics endpoint"""
        # Test different types
        analytics_types = ['overview', 'trends', 'citations', 'subjects', 'geographic']
        
        for analytics_type in analytics_types:
            data = self.test_endpoint(
                f"Optimized Analytics - {analytics_type.title()}",
                "GET",
                f"/api/analytics/?type={analytics_type}"
            )
            
            if data:
                self.log(f"Optimized analytics '{analytics_type}' successful", "INFO")
        
        # Test invalid type
        data = self.test_endpoint(
            "Optimized Analytics - Invalid Type",
            "GET",
            "/api/analytics/?type=invalid"
        )
        
        if data:
            assert 'error' in data, "Invalid type should return error"
    
    def test_export_data(self):
        """Test data export endpoint"""
        data = self.test_endpoint(
            "Export Data - JSON",
            "GET",
            "/api/export/"
        )
        
        if data:
            assert 'papers' in data, "Export should contain 'papers'"
            papers = data['papers']
            self.log(f"Export returned {len(papers)} papers", "INFO")
            
            if papers:
                # Check required fields in first paper
                required_fields = [
                    'record_id', 'title', 'author', 'journal',
                    'retraction_date', 'total_citations', 
                    'post_retraction_citations', 'post_retraction_percentage', 'reason'
                ]
                for field in required_fields:
                    assert field in papers[0], f"Paper should contain '{field}'"
    
    def test_warm_cache(self):
        """Test cache warming endpoint"""
        # Test analytics cache warming
        data = self.test_endpoint(
            "Warm Cache - Analytics",
            "POST",
            "/api/warm-cache/",
            data=json.dumps({"type": "analytics"}),
            headers={"Content-Type": "application/json"}
        )
        
        if data:
            assert data['status'] == 'success', "Cache warming should succeed"
            assert 'message' in data, "Response should contain message"
        
        # Test all cache warming
        data = self.test_endpoint(
            "Warm Cache - All",
            "POST",
            "/api/warm-cache/",
            data=json.dumps({"type": "all"}),
            headers={"Content-Type": "application/json"}
        )
    
    def test_response_times(self):
        """Test API response times"""
        self.log("Testing API response times...", "TEST")
        
        endpoints = [
            "/api/search-autocomplete/?q=science",
            "/api/analytics-realtime/",
            "/api/analytics/?type=overview",
            "/api/post-retraction-analytics/"
        ]
        
        response_times = []
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.make_request("GET", endpoint)
            end_time = time.time()
            
            if response and response.status_code == 200:
                response_time = end_time - start_time
                response_times.append(response_time)
                self.log(f"{endpoint}: {response_time:.3f}s", "INFO")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            self.log(f"Average response time: {avg_response_time:.3f}s", "INFO")
            
            if avg_response_time > 2.0:
                self.log("Warning: Average response time > 2 seconds", "WARNING")
    
    def test_error_handling(self):
        """Test API error handling"""
        self.log("Testing error handling...", "TEST")
        
        # Test non-existent endpoints
        self.test_endpoint(
            "Error Handling - Non-existent Endpoint",
            "GET",
            "/api/non-existent/",
            expected_status=404
        )
        
        # Test malformed requests
        response = self.make_request(
            "POST",
            "/api/warm-cache/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        if response:
            self.log(f"Malformed request returned status: {response.status_code}", "INFO")
    
    def run_all_tests(self):
        """Run all API tests"""
        self.log("🚀 Starting PRCT API Test Suite", "INFO")
        self.log(f"Testing against: {self.base_url}", "INFO")
        
        # Check if server is reachable
        try:
            response = self.make_request("GET", "/")
            if response is None or response.status_code >= 500:
                self.log("Server appears to be down or unreachable", "ERROR")
                return False
        except:
            self.log("Unable to connect to server", "ERROR")
            return False
        
        # Run individual test suites
        test_suites = [
            ("Search & Discovery", self.test_search_autocomplete),
            ("Paper Citations", self.test_paper_citations),
            ("Post-Retraction Analytics", self.test_post_retraction_analytics),
            ("Analytics Data", self.test_analytics_data),
            ("Real-time Analytics", self.test_analytics_realtime),
            ("Optimized Analytics", self.test_optimized_analytics),
            ("Data Export", self.test_export_data),
            ("Cache Warming", self.test_warm_cache),
            ("Response Times", self.test_response_times),
            ("Error Handling", self.test_error_handling)
        ]
        
        for suite_name, test_func in test_suites:
            self.log(f"\n📋 Running {suite_name} Tests", "INFO")
            try:
                test_func()
            except Exception as e:
                self.log(f"Test suite '{suite_name}' failed with error: {e}", "ERROR")
        
        # Print summary
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test results summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = total_tests - passed_tests
        
        self.log(f"\n📊 Test Summary", "INFO")
        self.log(f"Total Tests: {total_tests}", "INFO")
        self.log(f"Passed: {passed_tests}", "SUCCESS" if passed_tests > 0 else "INFO")
        self.log(f"Failed: {failed_tests}", "ERROR" if failed_tests > 0 else "INFO")
        
        if failed_tests > 0:
            self.log("\n❌ Failed Tests:", "ERROR")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    self.log(f"  - {result['name']}: {result.get('error', 'Unknown error')}", "ERROR")
        
        # Performance summary
        response_times = [r.get('response_time', 0) for r in self.test_results if r.get('response_time')]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            self.log(f"\n⚡ Performance Summary:", "INFO")
            self.log(f"Average Response Time: {avg_time:.3f}s", "INFO")
            self.log(f"Slowest Response: {max_time:.3f}s", "INFO")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.log(f"\n🎯 Success Rate: {success_rate:.1f}%", "SUCCESS" if success_rate >= 90 else "WARNING")
        
        return success_rate >= 90

def main():
    """Main function to run API tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PRCT API Testing Suite')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL for PRCT API (default: http://localhost:8000)')
    parser.add_argument('--production', action='store_true',
                       help='Test against production server (https://prct.xeradb.com)')
    
    args = parser.parse_args()
    
    if args.production:
        base_url = 'https://prct.xeradb.com'
    else:
        base_url = args.url
    
    tester = PRCTAPITester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 