#!/usr/bin/env python3
"""
PRCT Automatic Data Updater
Complete automation script for Retraction Watch data and citations
"""

import os
import sys
import subprocess
import requests
import shutil
import glob
import logging
from datetime import datetime
from pathlib import Path
import tempfile

class PRCTAutoUpdater:
    def __init__(self, prct_path="/var/www/prct"):
        self.prct_path = Path(prct_path)
        self.data_dir = self.prct_path / "data"
        self.venv_python = self.prct_path / "venv" / "bin" / "python"
        self.manage_py = self.prct_path / "manage.py"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Setup logging
        log_file = self.prct_path / "logs" / "auto_updater.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
            
    def download_retraction_watch_data(self):
        """Download the latest Retraction Watch CSV data"""
        self.log("🔍 Checking for latest Retraction Watch data...")
        
        # Official GitLab URL
        url = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retraction_watch_{timestamp}.csv"
        filepath = self.data_dir / filename
        
        try:
            # Download with resume capability
            self.log(f"📡 Downloading from: {url}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Save the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate the file
            if filepath.stat().st_size > 1000000:  # Should be >1MB
                self.log(f"✅ Downloaded: {filename} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")
                return filepath
            else:
                self.log(f"❌ Download too small: {filepath.stat().st_size} bytes")
                filepath.unlink()
                return None
                
        except Exception as e:
            self.log(f"❌ Download failed: {e}", "ERROR")
            if filepath.exists():
                filepath.unlink()
            return None
    
    def cleanup_old_rwd_files(self, keep_latest=True):
        """Remove old Retraction Watch data files, optionally keeping the latest"""
        self.log("🧹 Cleaning up old Retraction Watch files...")
        
        # Find all RWD files
        rwd_files = list(self.data_dir.glob("retraction_watch_*.csv"))
        rwd_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not rwd_files:
            self.log("No old RWD files to clean up")
            return
        
        # Keep the latest file, remove others
        files_to_remove = rwd_files[1:] if keep_latest else rwd_files
        
        for file_path in files_to_remove:
            try:
                file_path.unlink()
                self.log(f"🗑️  Removed old file: {file_path.name}")
            except Exception as e:
                self.log(f"❌ Could not remove {file_path.name}: {e}", "WARNING")
        
        if keep_latest and rwd_files:
            self.log(f"✅ Kept latest file: {rwd_files[0].name}")
    
    def get_latest_rwd_file(self):
        """Get the most recent Retraction Watch data file"""
        rwd_files = list(self.data_dir.glob("retraction_watch_*.csv"))
        if not rwd_files:
            return None
        
        # Return the most recent file
        latest_file = max(rwd_files, key=lambda x: x.stat().st_mtime)
        return latest_file
    
    def import_retraction_data(self, csv_file, limit=None):
        """Import retraction data using Django management command"""
        self.log(f"📊 Importing retraction data from {csv_file.name}...")
        
        try:
            cmd = [
                str(self.venv_python),
                str(self.manage_py),
                "import_retraction_watch",
                str(csv_file),
                "--update-existing"
            ]
            
            if limit:
                cmd.extend(["--limit", str(limit)])
            
            # Set environment
            env = os.environ.copy()
            env["DJANGO_SETTINGS_MODULE"] = "citing_retracted.settings_production"
            
            # Run the import
            result = subprocess.run(
                cmd,
                cwd=self.prct_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                self.log("✅ Retraction data import completed successfully")
                # Log key statistics from output
                for line in result.stdout.split('\n'):
                    if 'Records processed:' in line or 'Records created:' in line or 'Records updated:' in line:
                        self.log(f"   {line.strip()}")
                return True
            else:
                self.log(f"❌ Import failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Import error: {e}", "ERROR")
            return False
    
    def fetch_citations(self, limit=100):
        """Fetch citations for retracted papers using OpenCitations"""
        self.log(f"🔗 Fetching citations for up to {limit} papers...")
        
        try:
            cmd = [
                str(self.venv_python),
                str(self.manage_py),
                "fetch_citations",
                "--limit", str(limit)
            ]
            
            # Set environment
            env = os.environ.copy()
            env["DJANGO_SETTINGS_MODULE"] = "citing_retracted.settings_production"
            
            # Run citation fetching
            result = subprocess.run(
                cmd,
                cwd=self.prct_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.log("✅ Citation fetching completed successfully")
                # Log key statistics
                for line in result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['papers processed', 'citations found', 'total citations']):
                        self.log(f"   {line.strip()}")
                return True
            else:
                self.log(f"❌ Citation fetching failed: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("⏰ Citation fetching timed out after 1 hour", "WARNING")
            return False
        except Exception as e:
            self.log(f"❌ Citation fetching error: {e}", "ERROR")
            return False
    
    def fetch_citations_continuous(self, limit=100, batch_size=10, clear_cache_interval=20):
        """
        Fetch citations continuously with real-time database updates
        
        Args:
            limit: Maximum number of papers to process
            batch_size: Number of papers to process before showing progress
            clear_cache_interval: Clear cache every N papers for real-time updates
        """
        self.log(f"🔗 Starting continuous citation fetching for up to {limit} papers...")
        self.log(f"   📦 Batch size: {batch_size} papers")
        self.log(f"   🔄 Cache clear interval: every {clear_cache_interval} papers")
        
        try:
            total_processed = 0
            total_citations_found = 0
            total_new_citations = 0
            
            # Process in batches for continuous updates
            for start_idx in range(0, limit, batch_size):
                batch_limit = min(batch_size, limit - start_idx)
                
                self.log(f"📊 Processing batch {start_idx // batch_size + 1}: papers {start_idx + 1}-{start_idx + batch_limit}")
                
                # Fetch citations for this batch
                success, batch_stats = self._fetch_citations_batch(batch_limit, start_idx)
                
                if success:
                    batch_processed = batch_stats.get('papers_processed', 0)
                    batch_citations = batch_stats.get('citations_found', 0)
                    batch_new = batch_stats.get('new_citations', 0)
                    
                    total_processed += batch_processed
                    total_citations_found += batch_citations
                    total_new_citations += batch_new
                    
                    self.log(f"   ✅ Batch completed: {batch_processed} papers, {batch_citations} citations ({batch_new} new)")
                    
                    # Clear cache periodically for real-time visibility
                    if total_processed % clear_cache_interval == 0:
                        self.log(f"   🔄 Clearing cache for real-time updates (processed {total_processed} papers)")
                        self.clear_analytics_cache()
                    
                    # Small delay to prevent overwhelming the APIs
                    if start_idx + batch_size < limit:  # Don't sleep after last batch
                        import time
                        time.sleep(2)
                else:
                    self.log(f"   ❌ Batch failed, continuing with next batch...", "WARNING")
                
                # Show progress
                progress_pct = min(100, (total_processed / limit) * 100)
                self.log(f"📈 Progress: {progress_pct:.1f}% ({total_processed}/{limit} papers, {total_new_citations} new citations)")
            
            # Final cache clear and summary
            self.log("🔄 Final cache clear for complete data refresh...")
            self.clear_analytics_cache()
            
            self.log(f"✅ Continuous citation fetching completed!")
            self.log(f"   📄 Total papers processed: {total_processed}")
            self.log(f"   📈 Total citations found: {total_citations_found}")
            self.log(f"   ✨ New citations added: {total_new_citations}")
            self.log(f"   🌐 Citations are now visible in real-time on the website!")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Continuous citation fetching error: {e}", "ERROR")
            return False
    
    def _fetch_citations_batch(self, batch_size, offset=0):
        """Fetch citations for a specific batch of papers"""
        try:
            # Use a custom Django command that processes one paper at a time
            cmd = [
                str(self.venv_python),
                str(self.manage_py),
                "fetch_citations_realtime",
                "--batch-size", str(batch_size),
                "--offset", str(offset)
            ]
            
            # Set environment
            env = os.environ.copy()
            env["DJANGO_SETTINGS_MODULE"] = "citing_retracted.settings_production"
            
            # Run citation fetching for this batch
            result = subprocess.run(
                cmd,
                cwd=self.prct_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout per batch
            )
            
            if result.returncode == 0:
                # Parse statistics from output
                stats = {
                    'papers_processed': 0,
                    'citations_found': 0,
                    'new_citations': 0
                }
                
                for line in result.stdout.split('\n'):
                    if 'papers processed:' in line.lower():
                        try:
                            stats['papers_processed'] = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif 'citations found:' in line.lower():
                        try:
                            stats['citations_found'] = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif 'new citations:' in line.lower():
                        try:
                            stats['new_citations'] = int(line.split(':')[1].strip())
                        except:
                            pass
                
                return True, stats
            else:
                self.log(f"Batch fetch error: {result.stderr}", "ERROR")
                return False, {}
                
        except subprocess.TimeoutExpired:
            self.log("⏰ Batch citation fetching timed out", "WARNING")
            return False, {}
        except Exception as e:
            self.log(f"❌ Batch citation fetching error: {e}", "ERROR")
            return False, {}
    
    def clear_analytics_cache(self):
        """Clear analytics cache to show updated data"""
        self.log("🔄 Clearing analytics cache...")
        
        try:
            cmd = [
                str(self.venv_python),
                str(self.manage_py),
                "shell",
                "-c",
                """
from django.core.cache import cache
cache.delete('analytics_complex_data_v2')
cache.delete('analytics_basic_stats_v2')
print('✅ Analytics cache cleared!')
"""
            ]
            
            env = os.environ.copy()
            env["DJANGO_SETTINGS_MODULE"] = "citing_retracted.settings_production"
            
            result = subprocess.run(
                cmd,
                cwd=self.prct_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                self.log("✅ Analytics cache cleared successfully")
                return True
            else:
                self.log(f"❌ Cache clearing failed: {result.stderr}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Cache clearing error: {e}", "WARNING")
            return False
    
    def run_full_update(self, citation_limit=100, force_download=False, import_limit=None, continuous_citations=False):
        """Run complete update process"""
        self.log("🚀 Starting PRCT automatic update process...")
        
        success_count = 0
        
        # 1. Download latest Retraction Watch data
        if force_download or not self.get_latest_rwd_file():
            latest_file = self.download_retraction_watch_data()
            if latest_file:
                success_count += 1
                # Clean up old files after successful download
                self.cleanup_old_rwd_files(keep_latest=True)
            else:
                self.log("❌ Could not download RWD data, using existing file if available", "WARNING")
        else:
            latest_file = self.get_latest_rwd_file()
            self.log(f"📁 Using existing file: {latest_file.name}")
        
        # 2. Import retraction data
        if latest_file and latest_file.exists():
            if self.import_retraction_data(latest_file, limit=import_limit):
                success_count += 1
        else:
            self.log("❌ No RWD file available for import", "ERROR")
            return False
        
        # 3. Fetch citations (choose method based on continuous_citations flag)
        if continuous_citations:
            self.log("🔄 Using continuous citation fetching for real-time updates...")
            if self.fetch_citations_continuous(limit=citation_limit):
                success_count += 1
        else:
            self.log("📦 Using standard citation fetching...")
            if self.fetch_citations(limit=citation_limit):
                success_count += 1
        
        # 4. Clear analytics cache (only if not continuous, as continuous already clears cache)
        if not continuous_citations:
            if self.clear_analytics_cache():
                success_count += 1
        else:
            success_count += 1  # Already cleared during continuous process
        
        # 5. Summary
        self.log(f"📈 Update process completed: {success_count}/4 steps successful")
        
        if success_count >= 3:
            self.log("✅ Update process completed successfully!")
            return True
        else:
            self.log("⚠️  Update process completed with some failures", "WARNING")
            return False

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PRCT Automatic Data Updater')
    parser.add_argument('--prct-path', default='/var/www/prct',
                       help='Path to PRCT installation (default: /var/www/prct)')
    parser.add_argument('--citation-limit', type=int, default=100,
                       help='Number of papers to fetch citations for (default: 100)')
    parser.add_argument('--import-limit', type=int, default=None,
                       help='Limit number of records to import (default: unlimited)')
    parser.add_argument('--force-download', action='store_true',
                       help='Force download even if recent file exists')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Only clean up old files, no update')
    parser.add_argument('--continuous-citations', action='store_true',
                       help='Use continuous citation fetching for real-time website updates')
    
    args = parser.parse_args()
    
    updater = PRCTAutoUpdater(args.prct_path)
    
    if args.cleanup_only:
        updater.cleanup_old_rwd_files(keep_latest=True)
        return
    
    success = updater.run_full_update(
        citation_limit=args.citation_limit,
        force_download=args.force_download,
        import_limit=args.import_limit,
        continuous_citations=args.continuous_citations
    )
    
    if success:
        if args.continuous_citations:
            print("✅ PRCT update completed successfully with real-time citations!")
            print("🌐 Citations are updated continuously on the website!")
        else:
            print("✅ PRCT update completed successfully!")
    else:
        print("❌ PRCT update completed with errors!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 