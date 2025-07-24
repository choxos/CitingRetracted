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
                title = ''
                if 'title' in item and item['title']:
                    title = item['title'][0] if isinstance(item['title'], list) else str(item['title'])
                    # Clean title - remove excessive whitespace and line breaks
                    title = ' '.join(title.split())
                
                # Authors - clean formatting
                authors = []
                if 'author' in item:
                    for author in item['author'][:5]:  # Limit to first 5 authors
                        given = author.get('given', '').strip()
                        family = author.get('family', '').strip()
                        if given and family:
                            authors.append(f"{given} {family}")
                        elif family:
                            authors.append(family)
                        elif given:
                            authors.append(given)
                
                author_string = '; '.join(authors) if authors else ''
                
                # Journal/Container - clean formatting
                container_title = ''
                if 'container-title' in item and item['container-title']:
                    container_title = item['container-title'][0] if isinstance(item['container-title'], list) else str(item['container-title'])
                    container_title = ' '.join(container_title.split())
                
                # Publisher - clean formatting
                publisher = ''
                if 'publisher' in item:
                    publisher = str(item['publisher']).strip()
                    publisher = ' '.join(publisher.split())
                
                # DOI
                doi = item.get('DOI', '').strip()
                
                # Publication date - standardized format
                pub_date = ''
                date_source = item.get('published-print') or item.get('published-online') or item.get('created')
                if date_source and 'date-parts' in date_source:
                    date_parts = date_source['date-parts']
                    if date_parts and len(date_parts[0]) >= 3:
                        year, month, day = date_parts[0][:3]
                        pub_date = f"{month}/{day}/{year}"
                
                # Update information (retraction details)
                retraction_doi = ''
                retraction_date = ''
                
                if 'update-to' in item:
                    for update in item['update-to']:
                        if update.get('type') == 'retraction':
                            retraction_doi = update.get('DOI', '').strip()
                            if 'updated' in update and 'date-parts' in update['updated']:
                                date_parts = update['updated']['date-parts']
                                if date_parts and len(date_parts[0]) >= 3:
                                    year, month, day = date_parts[0][:3]
                                    retraction_date = f"{month}/{day}/{year}"
                
                # Subject classification - clean formatting
                subjects = []
                if 'subject' in item and item['subject']:
                    # Take first 3 subjects and clean them
                    for subject in item['subject'][:3]:
                        clean_subject = ' '.join(str(subject).split())
                        subjects.append(clean_subject)
                
                subject_string = '; '.join(subjects) if subjects else ''
                
                # Create clean record ID
                record_id = f"CR_{doi.replace('/', '_').replace('.', '_')}" if doi else f"CR_{len(converted) + 1:06d}"
                
                # Create record with cleaned data
                record = {
                    'Record ID': record_id,
                    'Title': title[:500],  # Limit title length
                    'Author': author_string[:300],  # Limit author string length
                    'Journal': container_title[:200],  # Limit journal name length
                    'Publisher': publisher[:100],  # Limit publisher name length
                    'Country': '',  # Not available in CrossRef API
                    'Institution': '',  # Would need to parse affiliations
                    'ArticleType': item.get('type', '').replace('-', ' ').title() if item.get('type') else '',
                    'Subject': subject_string[:200],  # Limit subject string length
                    'OriginalPaperDOI': doi,
                    'RetractionDOI': retraction_doi,
                    'OriginalPaperDate': pub_date,
                    'RetractionDate': retraction_date,
                    'Reason': 'Identified via CrossRef API',  # Standardized reason
                    'RetractionNature': 'Retraction',
                    'Paywalled': 'No',  # Default assumption for CrossRef data
                    'URLS': f"https://doi.org/{doi}" if doi else '',
                    'OriginalPaperPubMedID': '',  # Not typically available in CrossRef
                    'RetractionPubMedID': '',
                    'Notes': f"Fetched from CrossRef API on {datetime.now().strftime('%Y-%m-%d')}"
                }
                
                # Final cleanup - ensure no None values or problematic characters
                for key, value in record.items():
                    if value is None:
                        record[key] = ''
                    elif isinstance(value, str):
                        # Remove any remaining problematic characters
                        record[key] = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        # Ensure no double quotes in the middle of strings
                        if '"' in record[key] and not (record[key].startswith('"') and record[key].endswith('"')):
                            record[key] = record[key].replace('"', "'")
                
                converted.append(record)
                
            except Exception as e:
                self.log(f"⚠️  Error converting item: {e}")
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
        
        # Define exact fieldnames matching Retraction Watch format
        fieldnames = [
            'Record ID', 'Title', 'Subject', 'Institution', 'Journal', 'Publisher', 
            'Country', 'Author', 'URLS', 'ArticleType', 'RetractionDate', 
            'RetractionDOI', 'RetractionPubMedID', 'OriginalPaperDate', 
            'OriginalPaperDOI', 'OriginalPaperPubMedID', 'RetractionNature', 
            'Reason', 'Paywalled', 'Notes'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Use comma delimiter explicitly and handle quoting properly
                writer = csv.DictWriter(
                    csvfile, 
                    fieldnames=fieldnames,
                    delimiter=',',
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL
                )
                writer.writeheader()
                
                for record in retractions_data:
                    # Ensure all fields are present and properly formatted
                    row = {}
                    for field in fieldnames:
                        value = record.get(field, '')
                        
                        # Clean up the value - remove problematic characters
                        if isinstance(value, str):
                            # Remove newlines and carriage returns
                            value = value.replace('\n', ' ').replace('\r', ' ')
                            # Remove extra whitespace
                            value = ' '.join(value.split())
                            # Handle commas in content by ensuring proper quoting
                            if ',' in value and not (value.startswith('"') and value.endswith('"')):
                                value = f'"{value}"'
                        
                        row[field] = value
                    
                    writer.writerow(row)
            
            # Validate the generated CSV
            if self.validate_generated_csv(filename):
                self.log(f"✅ Saved {len(retractions_data)} retractions to {filename}")
                return filename
            else:
                self.log(f"❌ Generated CSV failed validation", "ERROR")
                return None
            
        except Exception as e:
            self.log(f"❌ Error saving CSV: {e}", "ERROR")
            return None
    
    def validate_generated_csv(self, filename):
        """Validate that the generated CSV can be read properly"""
        try:
            import csv
            with open(filename, 'r', encoding='utf-8') as f:
                # Test that CSV can be parsed
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                    self.log(f"🔍 CSV validation: delimiter='{dialect.delimiter}', quote='{dialect.quotechar}'")
                except:
                    self.log("⚠️  CSV sniffer failed, but proceeding...", "WARNING")
                
                # Try reading first few rows
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if first_row and 'Record ID' in first_row:
                    self.log("✅ CSV validation passed")
                    return True
                else:
                    self.log("❌ CSV validation failed - no Record ID found", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ CSV validation error: {e}", "ERROR")
            return False
    
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