#!/usr/bin/env python3
"""
Fetch Latest Retraction Watch Data
Downloads the most recent retraction database from Retraction Watch
"""

import requests
import os
import sys
from datetime import datetime
import pandas as pd

def fetch_retraction_watch_data():
    """Download the latest Retraction Watch database"""
    
    # Primary URL for Retraction Watch CSV
    urls = [
        "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false",
        "http://retractiondatabase.org/RetractionWatch.csv",
        "https://retractionwatch.com/retraction-watch-database/",
        "http://retractiondatabase.org/download/",
    ]
    
    print("🔍 Fetching latest Retraction Watch data...")
    
    for url in urls:
        try:
            print(f"📡 Trying: {url}")
            
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Check if it's actually CSV data
                content_type = response.headers.get('content-type', '').lower()
                
                if 'csv' in content_type or url.endswith('.csv'):
                    return save_csv_data(response.content, url)
                elif 'html' in content_type:
                    print(f"📄 Got HTML page, checking for download links...")
                    return parse_download_page(response.text, url)
                else:
                    print(f"⚠️  Unknown content type: {content_type}")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {url}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {url}: {e}")
            continue
    
    print("❌ Could not download from any source")
    return None

def save_csv_data(csv_content, source_url):
    """Save CSV data to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"retraction_watch_{timestamp}.csv"
    
    try:
        with open(filename, 'wb') as f:
            f.write(csv_content)
        
        # Validate the CSV
        df = pd.read_csv(filename)
        print(f"✅ Downloaded: {filename}")
        print(f"📊 Records: {len(df)} rows, {len(df.columns)} columns")
        print(f"🔗 Source: {source_url}")
        
        # Show sample columns
        print(f"📋 Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return None

def parse_download_page(html_content, base_url):
    """Parse HTML page to find download links"""
    from bs4 import BeautifulSoup
    import urllib.parse
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for download links
        download_links = []
        
        # Common patterns for download links
        patterns = [
            'a[href*="download"]',
            'a[href*=".csv"]',
            'a[href*="export"]',
            'a[href*="database"]',
            'a[text*="Download"]',
            'a[text*="CSV"]'
        ]
        
        for pattern in patterns:
            links = soup.select(pattern)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urllib.parse.urljoin(base_url, href)
                    download_links.append(full_url)
        
        if download_links:
            print(f"🔗 Found download links:")
            for i, link in enumerate(download_links[:3], 1):
                print(f"   {i}. {link}")
            
            # Try to download from the first link
            return fetch_from_url(download_links[0])
        else:
            print("❌ No download links found on page")
            return None
            
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return None

def fetch_from_url(url):
    """Fetch data from a specific URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            return save_csv_data(response.content, url)
        else:
            print(f"❌ Failed to download from {url}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading from {url}: {e}")
        return None

def main():
    """Main function"""
    print("🎯 Retraction Watch Data Fetcher")
    print("=" * 50)
    
    # Check if pandas and beautifulsoup4 are available
    try:
        import pandas as pd
        import bs4
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Install with: pip install pandas beautifulsoup4 requests")
        sys.exit(1)
    
    filename = fetch_retraction_watch_data()
    
    if filename:
        print(f"\n✅ Success! Downloaded: {filename}")
        print(f"📁 You can now import this file into your PRCT database")
        print(f"🚀 Next steps:")
        print(f"   1. Review the data structure")
        print(f"   2. Update your import script if needed")
        print(f"   3. Run: python manage.py import_retraction_data {filename}")
    else:
        print("\n❌ Failed to download Retraction Watch data")
        print("🔧 Manual options:")
        print("   1. Visit: http://retractiondatabase.org/")
        print("   2. Look for download/export functionality")
        print("   3. Download CSV manually")

if __name__ == "__main__":
    main() 