#!/usr/bin/env python3
"""
Complete Retraction Watch Database Update Pipeline
Downloads latest data and imports it into PRCT database
"""

import os
import sys
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import tempfile
import shutil


class RetractionDatabaseUpdater:
    def __init__(self, prct_path="/var/www/prct"):
        self.prct_path = Path(prct_path)
        self.data_dir = self.prct_path / "data"
        self.venv_python = self.prct_path / "venv" / "bin" / "python"
        self.manage_py = self.prct_path / "manage.py"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def download_retraction_watch_data(self):
        """Download the latest Retraction Watch CSV data"""
        self.log("🔍 Downloading latest Retraction Watch data...")
        
        urls = [
            "http://retractiondatabase.org/RetractionWatch.csv",
            "https://retractionwatch.com/retraction-watch-database/",
        ]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retraction_watch_{timestamp}.csv"
        filepath = self.data_dir / filename
        
        for url in urls:
            try:
                self.log(f"📡 Trying URL: {url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; PRCT-UpdateBot/1.0)',
                    'Accept': 'text/csv,text/html,application/xhtml+xml,*/*',
                }
                
                response = requests.get(url, headers=headers, timeout=60, stream=True)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'csv' in content_type or url.endswith('.csv'):
                        # Direct CSV download
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Validate the downloaded file
                        if self.validate_csv_file(filepath):
                            self.log(f"✅ Successfully downloaded: {filename}")
                            return filepath
                        else:
                            self.log("❌ Downloaded file failed validation")
                            filepath.unlink(missing_ok=True)
                            
                    else:
                        self.log("📄 Got HTML page, checking for download links...")
                        # Try to parse HTML for download links
                        download_url = self.parse_download_page(response.text, url)
                        if download_url:
                            return self.download_from_url(download_url, filepath)
                        
                else:
                    self.log(f"❌ HTTP {response.status_code} from {url}")
                    
            except Exception as e:
                self.log(f"❌ Error downloading from {url}: {e}", "ERROR")
                continue
        
        raise Exception("Could not download Retraction Watch data from any source")
    
    def parse_download_page(self, html_content, base_url):
        """Parse HTML page to find CSV download links"""
        try:
            from bs4 import BeautifulSoup
            import urllib.parse
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for download links
            selectors = [
                'a[href*="download"]',
                'a[href*=".csv"]',
                'a[href*="export"]',
                'a[href*="RetractionWatch"]'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and ('.csv' in href.lower() or 'download' in href.lower()):
                        full_url = urllib.parse.urljoin(base_url, href)
                        self.log(f"🔗 Found download link: {full_url}")
                        return full_url
                        
        except ImportError:
            self.log("⚠️  BeautifulSoup not available for HTML parsing", "WARNING")
        except Exception as e:
            self.log(f"❌ Error parsing HTML: {e}", "ERROR")
            
        return None
    
    def download_from_url(self, url, filepath):
        """Download CSV from a specific URL"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; PRCT-UpdateBot/1.0)'}
            response = requests.get(url, headers=headers, timeout=120, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if self.validate_csv_file(filepath):
                    self.log(f"✅ Successfully downloaded from: {url}")
                    return filepath
                    
            self.log(f"❌ Failed to download from {url}: HTTP {response.status_code}")
            
        except Exception as e:
            self.log(f"❌ Error downloading from {url}: {e}", "ERROR")
            
        return None
    
    def validate_csv_file(self, filepath):
        """Validate that the downloaded file is a proper CSV"""
        try:
            if not filepath.exists() or filepath.stat().st_size < 1000:
                return False
                
            # Check first few lines
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                first_line = f.readline().strip()
                
                # Should contain CSV headers
                expected_headers = ['Record ID', 'Title', 'Author', 'Journal']
                if any(header in first_line for header in expected_headers):
                    lines = sum(1 for _ in f) + 1  # +1 for first line already read
                    self.log(f"📊 CSV validation passed: {lines:,} lines")
                    return lines > 100  # Should have meaningful data
                    
        except Exception as e:
            self.log(f"❌ CSV validation failed: {e}", "ERROR")
            
        return False
    
    def setup_django_environment(self):
        """Set up Django environment variables"""
        os.chdir(self.prct_path)
        
        # Load environment variables from .env file
        env_file = self.prct_path / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Set Django settings
        os.environ['DJANGO_SETTINGS_MODULE'] = 'citing_retracted.production_settings'
        
        self.log("🔧 Django environment configured")
    
    def import_data_to_database(self, csv_filepath, dry_run=False, update_existing=True):
        """Import the CSV data into the database using Django management command"""
        self.log(f"📥 Importing data from {csv_filepath.name}...")
        
        cmd = [
            str(self.venv_python),
            str(self.manage_py),
            'import_retraction_watch',
            str(csv_filepath),
        ]
        
        if dry_run:
            cmd.append('--dry-run')
            self.log("🔍 Running in DRY RUN mode")
        
        if update_existing:
            cmd.append('--update-existing')
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.prct_path
            )
            
            if result.returncode == 0:
                self.log("✅ Import completed successfully")
                self.log("📊 Import output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log(f"   {line}")
                return True
            else:
                self.log(f"❌ Import failed with exit code {result.returncode}", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Import command failed: {e}", "ERROR")
            return False
    
    def fetch_citations(self, limit=None):
        """Fetch citations for papers after import"""
        self.log("🔍 Fetching citations for retracted papers...")
        
        cmd = [
            str(self.venv_python),
            str(self.manage_py),
            'fetch_citations',
        ]
        
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.prct_path
            )
            
            if result.returncode == 0:
                self.log("✅ Citation fetching completed")
                return True
            else:
                self.log(f"⚠️  Citation fetching had issues (exit code {result.returncode})", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Citation fetch failed: {e}", "ERROR")
            return False
    
    def cleanup_old_files(self, keep_recent=3):
        """Remove old CSV files, keeping only the most recent ones"""
        csv_files = sorted(self.data_dir.glob("retraction_watch_*.csv"))
        
        if len(csv_files) > keep_recent:
            for old_file in csv_files[:-keep_recent]:
                old_file.unlink()
                self.log(f"🗑️  Removed old file: {old_file.name}")
    
    def run_full_update(self, dry_run=False, fetch_citations_limit=100):
        """Run the complete update pipeline"""
        self.log("🚀 Starting Retraction Watch database update...")
        
        try:
            # 1. Setup environment
            self.setup_django_environment()
            
            # 2. Download latest data
            csv_file = self.download_retraction_watch_data()
            
            # 3. Import into database
            if self.import_data_to_database(csv_file, dry_run=dry_run):
                
                if not dry_run:
                    # 4. Fetch citations for new/updated papers
                    self.fetch_citations(limit=fetch_citations_limit)
                    
                    # 5. Cleanup old files
                    self.cleanup_old_files()
                
                self.log("🎉 Database update completed successfully!")
                return True
            else:
                self.log("❌ Database update failed during import", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Database update failed: {e}", "ERROR")
            return False


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Retraction Watch database')
    parser.add_argument('--prct-path', default='/var/www/prct', 
                       help='Path to PRCT installation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview import without making changes')
    parser.add_argument('--citations-limit', type=int, default=100,
                       help='Limit citations to fetch (default: 100)')
    parser.add_argument('--download-only', action='store_true',
                       help='Only download data, do not import')
    
    args = parser.parse_args()
    
    updater = RetractionDatabaseUpdater(args.prct_path)
    
    if args.download_only:
        try:
            csv_file = updater.download_retraction_watch_data()
            print(f"✅ Downloaded: {csv_file}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            sys.exit(1)
    else:
        success = updater.run_full_update(
            dry_run=args.dry_run, 
            fetch_citations_limit=args.citations_limit
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 