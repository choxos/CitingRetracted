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
    
    # Official GitLab URL - only source to use
    url = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false"
    
    print("🔍 Fetching latest Retraction Watch data...")
    print(f"📡 Using official GitLab source: {url}")
    
    # Set headers for polite usage
    headers = {
        'User-Agent': 'PRCT-DataBot/1.0 (compatible; retraction-tracker)',
        'Accept': 'text/csv,application/octet-stream,*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=120, stream=True)
        
        if response.status_code == 200:
            return save_csv_data(response.content, url)
        else:
            print(f"❌ HTTP {response.status_code}: {url}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
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

def main():
    """Main function"""
    print("🎯 Retraction Watch Data Fetcher")
    print("=" * 50)
    
    # Check if pandas is available
    try:
        import pandas as pd
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Install with: pip install pandas requests")
        sys.exit(1)
    
    filename = fetch_retraction_watch_data()
    
    if filename:
        print(f"\n✅ Success! Downloaded: {filename}")
        print(f"📁 You can now import this file into your PRCT database")
        print(f"🚀 Next steps:")
        print(f"   1. Review the data structure")
        print(f"   2. Update your import script if needed")
        print(f"   3. Run: python manage.py import_retraction_watch {filename}")
    else:
        print("\n❌ Failed to download Retraction Watch data")
        print("🔧 Manual alternative:")
        print("   Use: wget -c -O retraction_watch.csv \\")
        print("        'https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false'")
        print("   Or visit: https://gitlab.com/crossref/retraction-watch-data/")


if __name__ == "__main__":
    main() 