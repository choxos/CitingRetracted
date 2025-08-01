import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date
from papers.models import RetractedPaper, DataImportLog


class Command(BaseCommand):
    help = 'Import retracted papers from Retraction Watch CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without saving to database'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of records to process'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing records if they already exist'
        )

    def parse_date(self, date_str):
        """Parse date string in various formats including the new Retraction Watch format."""
        if not date_str or date_str.lower() in ['', 'unknown', 'n/a', 'null']:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Handle the new format "7/29/2024 0:00"
        if ' 0:00' in date_str:
            date_str = date_str.replace(' 0:00', '')
        
        # Also handle other time formats that might be present
        if ' 00:00' in date_str:
            date_str = date_str.replace(' 00:00', '')
        
        # Common date formats in Retraction Watch data
        date_formats = [
            '%m/%d/%Y',     # New format: 2/25/2025
            '%Y-%m-%d',     # ISO format
            '%d/%m/%Y',     # European format
            '%Y',           # Year only
            '%m/%Y',        # Month/Year
            '%d-%m-%Y',     # Day-Month-Year
            '%Y-%m',        # Year-Month
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return parsed_date
            except ValueError:
                continue
        
        # If no format works, log and return None
        self.stdout.write(
            self.style.WARNING(f"Could not parse date: {date_str}")
        )
        return None
    
    def parse_boolean(self, value):
        """Parse boolean values from CSV."""
        if not value:
            return False
        value = value.lower().strip()
        return value in ['yes', 'true', '1', 'y']
    
    def is_open_access(self, paywalled_value):
        """Determine if paper is open access based on Paywalled column."""
        if not paywalled_value:
            return False  # Unknown, assume not open access
        
        paywalled_str = str(paywalled_value).lower().strip()
        
        # If Paywalled == "No", then it's open access
        if paywalled_str in ['no', 'n', 'false', '0']:
            return True
        # If Paywalled == "Yes", then it's not open access  
        elif paywalled_str in ['yes', 'y', 'true', '1']:
            return False
        else:
            return False  # Default to not open access for unknown values
    
    def clean_field(self, value):
        """Clean field values."""
        if not value:
            return ''
        return value.strip().replace('\n', ' ').replace('\r', '')
    
    def extract_subjects(self, subject_str):
        """Extract and clean subject classifications."""
        if not subject_str:
            return ''
        
        # Remove prefix codes and clean up
        subjects = []
        for subject in subject_str.split(';'):
            subject = subject.strip()
            if ')' in subject:
                # Remove prefix like "(PHY) " or "(B/T) "
                subject = subject.split(')', 1)[1].strip()
            if subject:
                subjects.append(subject)
        
        return '; '.join(subjects)
    
    def clean_article_type(self, article_type_str):
        """Clean article type field."""
        if not article_type_str:
            return ''
        # Remove trailing semicolons
        return article_type_str.strip().rstrip(';')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        limit = options['limit']
        update_existing = options['update_existing']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f"File not found: {csv_file}")
            )
            return

        # Create import log
        import_log = DataImportLog.objects.create(
            import_type='retraction_watch',
            start_time=timezone.now(),
            status='running'
        )

        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_failed = 0

            with open(csv_file, 'r', encoding='utf-8', errors='replace') as file:
                # Retraction Watch CSV files are always comma-delimited
                # Don't rely on sniffer as it can incorrectly detect other characters
                delimiter = ','
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                # Debug: Print headers and first row
                headers = reader.fieldnames
                if headers:
                    self.stdout.write(f"DEBUG: Detected {len(headers)} columns: {headers[:5]}...")
                    if 'Record ID' in headers:
                        self.stdout.write("DEBUG: 'Record ID' column found ✓")
                    else:
                        self.stdout.write(f"DEBUG: 'Record ID' column NOT found! Available columns: {headers}")
                
                for row in reader:
                    if limit and records_processed >= limit:
                        break
                    
                    try:
                        record_id = self.clean_field(row.get('Record ID', ''))
                        
                        # Debug: Print first few record IDs
                        if records_processed < 3:
                            self.stdout.write(f"DEBUG: Row {records_processed + 1} - Raw Record ID: {repr(row.get('Record ID', 'KEY_NOT_FOUND'))}")
                            self.stdout.write(f"DEBUG: Row {records_processed + 1} - Cleaned Record ID: {repr(record_id)}")
                        
                        if not record_id:
                            self.stdout.write(
                                self.style.WARNING(f"Skipping row without Record ID")
                            )
                            records_failed += 1
                            continue

                        # Check if record exists
                        existing_paper = None
                        if update_existing:
                            try:
                                existing_paper = RetractedPaper.objects.get(record_id=record_id)
                            except RetractedPaper.DoesNotExist:
                                pass

                        # Create or update paper with all new fields
                        paper_data = {
                            'title': self.clean_field(row.get('Title', '')),
                            'author': self.clean_field(row.get('Author', '')),
                            'journal': self.clean_field(row.get('Journal', '')),
                            'publisher': self.clean_field(row.get('Publisher', '')),
                            'institution': self.clean_field(row.get('Institution', '')),
                            'country': self.clean_field(row.get('Country', '')),
                            'article_type': self.clean_article_type(row.get('ArticleType', '')),
                            'subject': self.extract_subjects(row.get('Subject', '')),
                            'original_paper_doi': self.clean_field(row.get('OriginalPaperDOI', '')),
                            'retraction_doi': self.clean_field(row.get('RetractionDOI', '')),
                            'urls': self.clean_field(row.get('URLS', '')),
                            'original_paper_pubmed_id': self.clean_field(row.get('OriginalPaperPubMedID', '')),
                            'retraction_pubmed_id': self.clean_field(row.get('RetractionPubMedID', '')),
                            'retraction_nature': self.clean_field(row.get('RetractionNature', '')),
                            'reason': self.clean_field(row.get('Reason', '')),
                            'notes': self.clean_field(row.get('Notes', '')),
                            'paywalled': self.parse_boolean(row.get('Paywalled', '')),
                            'is_open_access': self.is_open_access(row.get('Paywalled', '')),
                            'original_paper_date': self.parse_date(row.get('OriginalPaperDate', '')),
                            'retraction_date': self.parse_date(row.get('RetractionDate', '')),
                        }

                        if not dry_run:
                            if existing_paper:
                                # Update existing record
                                for field, value in paper_data.items():
                                    setattr(existing_paper, field, value)
                                existing_paper.save()
                                records_updated += 1
                                self.stdout.write(f"Updated: {record_id}")
                            else:
                                # Create new record
                                paper_data['record_id'] = record_id
                                RetractedPaper.objects.create(**paper_data)
                                records_created += 1
                                self.stdout.write(f"Created: {record_id}")
                        else:
                            # Dry run - just show what would be created/updated
                            action = "UPDATE" if existing_paper else "CREATE"
                            self.stdout.write(f"[DRY RUN] {action}: {record_id} - {paper_data['title'][:50]}...")
                            records_created += 1

                        records_processed += 1

                        if records_processed % 100 == 0:
                            self.stdout.write(f"Processed {records_processed} records...")

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing record {record_id}: {str(e)}")
                        )
                        records_failed += 1
                        continue

            # Update import log
            import_log.end_time = timezone.now()
            import_log.status = 'completed'
            import_log.records_processed = records_processed
            import_log.records_created = records_created
            import_log.records_updated = records_updated
            import_log.records_failed = records_failed
            import_log.save()

            # Output summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nImport completed:\n"
                    f"  Records processed: {records_processed}\n"
                    f"  Records created: {records_created}\n"
                    f"  Records updated: {records_updated}\n"
                    f"  Records failed: {records_failed}\n"
                    f"  Dry run: {dry_run}"
                )
            )

        except Exception as e:
            import_log.end_time = timezone.now()
            import_log.status = 'failed'
            import_log.error_message = str(e)
            import_log.save()
            
            self.stdout.write(
                self.style.ERROR(f"Import failed: {str(e)}")
            )
            raise 