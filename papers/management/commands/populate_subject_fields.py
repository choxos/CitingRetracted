from django.core.management.base import BaseCommand
from papers.models import RetractedPaper
from django.db import transaction


class Command(BaseCommand):
    help = 'Populate broad_subjects and specific_fields from existing subject data'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        papers_to_update = RetractedPaper.objects.exclude(subject__isnull=True).exclude(subject__exact='')
        total_papers = papers_to_update.count()
        
        self.stdout.write(f'Found {total_papers} papers with subject data to process')
        
        processed = 0
        updated = 0
        
        for i in range(0, total_papers, batch_size):
            batch = papers_to_update[i:i + batch_size]
            
            with transaction.atomic():
                papers_to_save = []
                
                for paper in batch:
                    broad_subjects = []
                    specific_fields = []
                    
                    if paper.subject:
                        # Split by semicolon and clean up
                        subjects = [s.strip() for s in paper.subject.split(';') if s.strip()]
                        
                        for subject in subjects:
                            # Handle format: (ABBR) Field Name
                            if subject.startswith('(') and ')' in subject:
                                end_paren = subject.find(')')
                                abbr = subject[1:end_paren].strip()
                                field = subject[end_paren + 1:].strip()
                                
                                # Map abbreviations to full names
                                broad_category = self._expand_subject_abbreviation(abbr)
                                broad_subjects.append(broad_category)
                                specific_fields.append(field if field else 'General')
                                
                            # Handle format: Broad Category - Specific Field
                            elif ' - ' in subject:
                                parts = subject.split(' - ', 1)
                                broad_category = parts[0].strip()
                                specific_field = parts[1].strip()
                                broad_subjects.append(broad_category)
                                specific_fields.append(specific_field)
                                
                            # Handle single category
                            else:
                                broad_subjects.append(subject)
                                specific_fields.append('General')
                    
                    # Remove duplicates while preserving order
                    broad_subjects = list(dict.fromkeys(broad_subjects))
                    specific_fields = list(dict.fromkeys(specific_fields))
                    
                    new_broad = '; '.join(broad_subjects) if broad_subjects else ''
                    new_specific = '; '.join(specific_fields) if specific_fields else ''
                    
                    # Only update if there's a change
                    if paper.broad_subjects != new_broad or paper.specific_fields != new_specific:
                        paper.broad_subjects = new_broad
                        paper.specific_fields = new_specific
                        papers_to_save.append(paper)
                        updated += 1
                    
                    processed += 1
                    
                    if processed % 100 == 0:
                        self.stdout.write(f'Processed {processed}/{total_papers} papers...')
                
                if not dry_run and papers_to_save:
                    RetractedPaper.objects.bulk_update(papers_to_save, ['broad_subjects', 'specific_fields'])
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN: Would update {updated} out of {processed} papers'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} out of {processed} papers'))
        
        # Show some examples
        if updated > 0:
            examples = RetractedPaper.objects.exclude(broad_subjects__exact='').exclude(specific_fields__exact='')[:5]
            self.stdout.write('\nExamples of processed data:')
            for paper in examples:
                self.stdout.write(f'  Original: {paper.subject}')
                self.stdout.write(f'  Broad: {paper.broad_subjects}')
                self.stdout.write(f'  Fields: {paper.specific_fields}')
                self.stdout.write('')

    def _expand_subject_abbreviation(self, abbr):
        """Expand subject abbreviations to full names"""
        abbreviation_map = {
            'HSC': 'Health Sciences',
            'BLS': 'Biological and Life Sciences',
            'PSE': 'Physical Sciences and Engineering',
            'SSH': 'Social Sciences and Humanities',
            'CS': 'Computer Science',
            'MATH': 'Mathematics',
            'ENVS': 'Environmental Sciences',
            'AGRI': 'Agriculture',
            'EDU': 'Education',
            'BUS': 'Business',
            'LAW': 'Law',
            'ART': 'Arts',
            'MED': 'Medicine',
            'BIO': 'Biology',
            'CHEM': 'Chemistry',
            'PHYS': 'Physics',
            'PSYCH': 'Psychology',
            'SOC': 'Sociology',
        }
        return abbreviation_map.get(abbr.upper(), abbr) 