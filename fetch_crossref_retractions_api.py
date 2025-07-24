#!/usr/bin/env python3
"""
Fetch Retraction Data via CrossRef REST API
Real-time incremental updates from CrossRef API
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import time


class CrossRefRetractionsAPI:
    def __init__(self, email="your-email@domain.com"):
        self.base_url = "https://api.crossref.org/v1/works"
        self.email = email
        self.session = requests.Session()
        
        # Set polite headers as recommended by CrossRef
        self.session.headers.update({
            'User-Agent': f'PRCT-RetractionsBot/1.0 (mailto:{email})',
            'Accept': 'application/json'
        })
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def fetch_retractions(self, rows=100, offset=0, from_date=None, until_date=None):
        """
        Fetch retractions from CrossRef API
        
        Args:
            rows: Number of results per request (max 1000)
            offset: Offset for pagination
            from_date: Only retractions from this date onwards (YYYY-MM-DD)
            until_date: Only retractions until this date (YYYY-MM-DD)
        """
        
        params = {
            'filter': 'update-type:retraction',
            'rows': min(rows, 1000),  # CrossRef max is 1000
            'offset': offset,
            'mailto': self.email
        }
        
        # Add date filters if provided
        if from_date:
            params['filter'] += f',from-update-date:{from_date}'
        if until_date:
            params['filter'] += f',until-update-date:{until_date}'
            
        try:
            self.log(f"📡 Fetching retractions (rows={rows}, offset={offset})")
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'ok':
                message = data['message']
                total_results = message['total-results']
                items = message['items']
                
                self.log(f"✅ Found {len(items)} retractions (total available: {total_results:,})")
                return {
                    'items': items,
                    'total_results': total_results,
                    'items_per_page': message['items-per-page'],
                    'query': message['query']
                }
            else:
                self.log(f"❌ API returned error status: {data['status']}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ API request failed: {e}", "ERROR")
            return None
        except json.JSONDecodeError as e:
            self.log(f"❌ Failed to parse JSON response: {e}", "ERROR")
            return None
    
    def fetch_all_retractions(self, batch_size=100, max_results=None, from_date=None):
        """
        Fetch all available retractions with pagination
        
        Args:
            batch_size: Number of results per API call
            max_results: Maximum total results to fetch (None for all)
            from_date: Only retractions from this date onwards
        """
        
        all_retractions = []
        offset = 0
        
        while True:
            # Determine how many to fetch in this batch
            rows = batch_size
            if max_results and (offset + batch_size) > max_results:
                rows = max_results - offset
                
            if rows <= 0:
                break
                
            # Fetch batch
            result = self.fetch_retractions(
                rows=rows, 
                offset=offset, 
                from_date=from_date
            )
            
            if not result or not result['items']:
                break
                
            all_retractions.extend(result['items'])
            
            # Check if we've got all available results
            total_available = result['total_results']
            if offset + len(result['items']) >= total_available:
                break
                
            offset += len(result['items'])
            
            # Be polite to CrossRef API
            time.sleep(0.1)
            
            if max_results and len(all_retractions) >= max_results:
                all_retractions = all_retractions[:max_results]
                break
        
        self.log(f"📊 Fetched {len(all_retractions)} total retractions")
        return all_retractions
    
    def convert_to_retraction_watch_format(self, crossref_items):
        """
        Convert CrossRef API data to Retraction Watch CSV format
        """
        
        converted = []
        
        for item in crossref_items:
            try:
                # Extract basic information
                title = item.get('title', [''])[0] if item.get('title') else ''
                
                # Authors
                authors = []
                if 'author' in item:
                    for author in item['author']:
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given and family:
                            authors.append(f"{given} {family}")
                        elif family:
                            authors.append(family)
                
                # Journal/Container
                container_title = ''
                if 'container-title' in item and item['container-title']:
                    container_title = item['container-title'][0]
                
                # Publisher
                publisher = item.get('publisher', '')
                
                # DOI
                doi = item.get('DOI', '')
                
                # Publication date
                pub_date = ''
                if 'published-print' in item:
                    date_parts = item['published-print'].get('date-parts', [[]])
                    if date_parts and len(date_parts[0]) >= 3:
                        year, month, day = date_parts[0][:3]
                        pub_date = f"{month}/{day}/{year}"
                elif 'published-online' in item:
                    date_parts = item['published-online'].get('date-parts', [[]])
                    if date_parts and len(date_parts[0]) >= 3:
                        year, month, day = date_parts[0][:3]
                        pub_date = f"{month}/{day}/{year}"
                
                # Update information (retraction details)
                retraction_doi = ''
                retraction_date = ''
                
                if 'update-to' in item:
                    for update in item['update-to']:
                        if update.get('type') == 'retraction':
                            retraction_doi = update.get('DOI', '')
                            if 'updated' in update:
                                date_parts = update['updated'].get('date-parts', [[]])
                                if date_parts and len(date_parts[0]) >= 3:
                                    year, month, day = date_parts[0][:3]
                                    retraction_date = f"{month}/{day}/{year}"
                
                # Subject classification
                subjects = []
                if 'subject' in item:
                    subjects = item['subject']
                
                # Create record
                record = {
                    'Record ID': f"CR_{doi.replace('/', '_').replace('.', '_')}" if doi else f"CR_{len(converted)}",
                    'Title': title,
                    'Author': '; '.join(authors),
                    'Journal': container_title,
                    'Publisher': publisher,
                    'Country': '',  # Not available in CrossRef API
                    'Institution': '',  # Would need to parse affiliations
                    'ArticleType': item.get('type', '').title(),
                    'Subject': '; '.join(subjects),
                    'OriginalPaperDOI': doi,
                    'RetractionDOI': retraction_doi,
                    'OriginalPaperDate': pub_date,
                    'RetractionDate': retraction_date,
                    'Reason': 'Identified via CrossRef API',  # CrossRef doesn't provide detailed reasons
                    'RetractionNature': 'Retraction',
                    'Paywalled': 'Unknown',
                    'URLS': f"https://doi.org/{doi}" if doi else '',
                    'OriginalPaperPubMedID': '',  # Not available in CrossRef
                    'RetractionPubMedID': '',
                    'Notes': f"Fetched from CrossRef API on {datetime.now().strftime('%Y-%m-%d')}"
                }
                
                converted.append(record)
                
            except Exception as e:
                print(f"⚠️  Error converting item: {e}")
                continue
        
        return converted
    
    def save_as_csv(self, retractions_data, filename=None):
        """Save retraction data as CSV file"""
        import csv
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crossref_retractions_{timestamp}.csv"
        
        if not retractions_data:
            self.log("❌ No data to save", "ERROR")
            return None
        
        # Get all possible fieldnames
        fieldnames = [
            'Record ID', 'Title', 'Subject', 'Institution', 'Journal', 'Publisher', 
            'Country', 'Author', 'URLS', 'ArticleType', 'RetractionDate', 
            'RetractionDOI', 'RetractionPubMedID', 'OriginalPaperDate', 
            'OriginalPaperDOI', 'OriginalPaperPubMedID', 'RetractionNature', 
            'Reason', 'Paywalled', 'Notes'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in retractions_data:
                    # Ensure all fields are present
                    row = {field: record.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            self.log(f"✅ Saved {len(retractions_data)} retractions to {filename}")
            return filename
            
        except Exception as e:
            self.log(f"❌ Error saving CSV: {e}", "ERROR")
            return None
    
    def fetch_recent_retractions(self, days_back=7):
        """Fetch retractions from the last N days"""
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        self.log(f"🔍 Fetching retractions from last {days_back} days (since {from_date})")
        
        crossref_data = self.fetch_all_retractions(
            batch_size=100,
            max_results=1000,  # Reasonable limit for recent data
            from_date=from_date
        )
        
        if not crossref_data:
            self.log("❌ No recent retractions found")
            return None
        
        # Convert to Retraction Watch format
        converted_data = self.convert_to_retraction_watch_format(crossref_data)
        
        return converted_data


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch retractions via CrossRef API')
    parser.add_argument('--email', default='your-email@domain.com',
                       help='Your email for CrossRef API (polite usage)')
    parser.add_argument('--rows', type=int, default=100,
                       help='Number of results to fetch')
    parser.add_argument('--recent-days', type=int, default=7,
                       help='Fetch retractions from last N days')
    parser.add_argument('--all', action='store_true',
                       help='Fetch all available retractions (large dataset)')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename')
    parser.add_argument('--from-date', type=str,
                       help='Fetch retractions from date (YYYY-MM-DD)')
    parser.add_argument('--max-results', type=int,
                       help='Maximum number of results to fetch')
    
    args = parser.parse_args()
    
    api = CrossRefRetractionsAPI(email=args.email)
    
    if args.all:
        # Fetch all retractions
        api.log("🚀 Fetching ALL retractions from CrossRef API (this may take a while)")
        crossref_data = api.fetch_all_retractions(
            batch_size=100,
            max_results=args.max_results,
            from_date=args.from_date
        )
    elif args.recent_days:
        # Fetch recent retractions
        converted_data = api.fetch_recent_retractions(days_back=args.recent_days)
        if converted_data:
            filename = api.save_as_csv(converted_data, args.output)
            if filename:
                print(f"✅ Success! Saved to: {filename}")
                return
        print("❌ Failed to fetch recent retractions")
        sys.exit(1)
    else:
        # Fetch specified number of retractions
        result = api.fetch_retractions(
            rows=args.rows,
            from_date=args.from_date
        )
        if result:
            crossref_data = result['items']
        else:
            print("❌ Failed to fetch retractions")
            sys.exit(1)
    
    # Convert and save for non-recent fetches
    if 'crossref_data' in locals():
        converted_data = api.convert_to_retraction_watch_format(crossref_data)
        filename = api.save_as_csv(converted_data, args.output)
        
        if filename:
            print(f"✅ Success! Saved {len(converted_data)} retractions to: {filename}")
            print(f"📊 Ready for import with: python manage.py import_retraction_watch {filename}")
        else:
            print("❌ Failed to save CSV file")
            sys.exit(1)


if __name__ == "__main__":
    main() 