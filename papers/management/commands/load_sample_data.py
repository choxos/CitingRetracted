from django.core.management.base import BaseCommand
from django.utils import timezone
from papers.models import RetractedPaper, CitingPaper, Citation, DataImportLog
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Load sample data for testing PRCT with realistic retracted papers and citations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--papers',
            type=int,
            default=50,
            help='Number of retracted papers to create (default: 50)'
        )
        parser.add_argument(
            '--citations-per-paper',
            type=int,
            default=20,
            help='Average citations per paper (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample data before loading new data'
        )

    def handle(self, *args, **options):
        papers_count = options['papers']
        citations_per_paper = options['citations_per_paper']
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write(self.style.WARNING('🗑️ Clearing existing sample data...'))
            # Delete citations first (foreign key constraint)
            deleted_citations = Citation.objects.filter(source_api='sample_data').delete()
            # Delete citing papers
            deleted_citing = CitingPaper.objects.filter(source_api='sample_data').delete()
            # Delete retracted papers that look like sample data
            deleted_papers = RetractedPaper.objects.filter(record_id__startswith='SAMPLE').delete()
            
            self.stdout.write(f'   Deleted: {deleted_citations[0]} citations, {deleted_citing[0]} citing papers, {deleted_papers[0]} retracted papers')
        
        self.stdout.write(self.style.SUCCESS(f'🧪 Loading sample data: {papers_count} papers with ~{citations_per_paper} citations each...'))
        
        # Sample data arrays
        journals = [
            'Nature', 'Science', 'Cell', 'The Lancet', 'New England Journal of Medicine',
            'PNAS', 'Nature Medicine', 'Journal of Clinical Investigation', 'JAMA',
            'BMJ', 'Cell Metabolism', 'Immunity', 'Cancer Cell', 'Neuron',
            'Nature Genetics', 'PLoS ONE', 'Scientific Reports', 'eLife',
            'Journal of Biological Chemistry', 'Molecular Cell'
        ]
        
        publishers = [
            'Nature Publishing Group', 'American Association for the Advancement of Science',
            'Cell Press', 'Elsevier', 'Wiley', 'American Medical Association',
            'BMJ Publishing Group', 'Public Library of Science', 'Oxford University Press',
            'Cambridge University Press', 'Springer Nature', 'Frontiers Media'
        ]
        
        subjects = [
            'Medicine', 'Biology', 'Chemistry', 'Physics', 'Neuroscience',
            'Cancer Research', 'Immunology', 'Genetics', 'Biochemistry',
            'Molecular Biology', 'Cell Biology', 'Pharmacology', 'Cardiology',
            'Oncology', 'Microbiology', 'Epidemiology', 'Public Health',
            'Clinical Medicine', 'Biomedical Research', 'Life Sciences'
        ]
        
        broad_subjects = [
            'Life Sciences', 'Physical Sciences', 'Medical Sciences',
            'Biological Sciences', 'Health Sciences', 'Chemical Sciences'
        ]
        
        countries = [
            'United States', 'China', 'Germany', 'United Kingdom', 'Japan',
            'Canada', 'France', 'Italy', 'Australia', 'Netherlands',
            'Switzerland', 'South Korea', 'Sweden', 'India', 'Spain'
        ]
        
        institutions = [
            'Harvard University', 'Stanford University', 'MIT', 'University of Cambridge',
            'Oxford University', 'Yale University', 'University of California',
            'Johns Hopkins University', 'University of Pennsylvania', 'Columbia University',
            'University of Tokyo', 'Max Planck Institute', 'CNRS', 'University of Toronto',
            'ETH Zurich', 'Karolinska Institute', 'University of Melbourne'
        ]
        
        retraction_reasons = [
            'Data fabrication', 'Data falsification', 'Plagiarism', 'Duplicate publication',
            'Ethical violations', 'Research misconduct', 'Unreliable data',
            'Undisclosed conflicts of interest', 'Fake peer review',
            'Image manipulation', 'Statistical errors', 'Unethical experimentation',
            'Copyright infringement', 'Authorship disputes', 'Invalid methodology'
        ]
        
        article_types = [
            'Research Article', 'Review', 'Letter', 'Brief Communication',
            'Case Report', 'Editorial', 'Commentary', 'Clinical Trial',
            'Meta-analysis', 'Systematic Review'
        ]
        
        # Sample author names
        first_names = [
            'John', 'Mary', 'David', 'Sarah', 'Michael', 'Lisa', 'Robert', 'Jennifer',
            'William', 'Linda', 'Richard', 'Elizabeth', 'Joseph', 'Susan', 'Thomas',
            'Jessica', 'Christopher', 'Karen', 'Daniel', 'Nancy', 'Matthew', 'Betty',
            'Anthony', 'Helen', 'Mark', 'Sandra', 'Donald', 'Donna', 'Steven', 'Carol'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
            'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King'
        ]
        
        # Create sample retracted papers
        created_papers = 0
        created_citations = 0
        
        self.stdout.write('📄 Creating retracted papers...')
        
        for i in range(papers_count):
            # Generate realistic data
            retraction_date = timezone.now().date() - timedelta(days=random.randint(30, 3650))  # 1 month to 10 years ago
            original_date = retraction_date - timedelta(days=random.randint(365, 5475))  # 1-15 years before retraction
            
            # Generate authors (1-8 authors)
            num_authors = random.randint(1, 8)
            authors = []
            for _ in range(num_authors):
                first = random.choice(first_names)
                last = random.choice(last_names)
                authors.append(f"{first} {last}")
            
            # Generate title
            title_templates = [
                "Novel insights into {subject} mechanisms in {disease}",
                "Advanced {method} for studying {biological_process}",
                "Therapeutic potential of {compound} in {condition}",
                "Molecular basis of {phenomenon} in {organism}",
                "Clinical trial of {treatment} for {disease}",
                "Genetic factors influencing {trait} development",
                "Comprehensive analysis of {pathway} regulation",
                "Innovative approach to {problem} using {technique}",
                "Role of {protein} in {cellular_process}",
                "Epidemiological study of {factor} and {outcome}"
            ]
            
            title_vars = {
                'subject': random.choice(['protein', 'gene', 'enzyme', 'receptor', 'pathway']),
                'disease': random.choice(['cancer', 'diabetes', 'Alzheimer\'s', 'cardiovascular disease']),
                'method': random.choice(['CRISPR', 'mass spectrometry', 'imaging', 'sequencing']),
                'biological_process': random.choice(['cell division', 'apoptosis', 'metabolism', 'signal transduction']),
                'compound': random.choice(['drug X', 'compound Y', 'therapy Z', 'treatment A']),
                'condition': random.choice(['arthritis', 'depression', 'hypertension', 'inflammation']),
                'phenomenon': random.choice(['resistance', 'adaptation', 'differentiation', 'migration']),
                'organism': random.choice(['mice', 'humans', 'rats', 'cell lines']),
                'treatment': random.choice(['immunotherapy', 'gene therapy', 'drug treatment', 'surgery']),
                'trait': random.choice(['intelligence', 'height', 'disease susceptibility', 'longevity']),
                'pathway': random.choice(['metabolic', 'signaling', 'inflammatory', 'immune']),
                'problem': random.choice(['drug resistance', 'tumor growth', 'infection', 'aging']),
                'technique': random.choice(['AI', 'machine learning', 'nanotechnology', 'biotechnology']),
                'protein': random.choice(['p53', 'BRCA1', 'insulin', 'hemoglobin']),
                'cellular_process': random.choice(['autophagy', 'mitosis', 'transcription', 'translation']),
                'factor': random.choice(['diet', 'exercise', 'genetics', 'environment']),
                'outcome': random.choice(['mortality', 'disease risk', 'recovery', 'quality of life'])
            }
            
            title = random.choice(title_templates).format(**title_vars)
            
            paper = RetractedPaper.objects.create(
                record_id=f"SAMPLE{random.randint(10000, 99999)}_{i}",
                title=title,
                author='; '.join(authors),
                journal=random.choice(journals),
                publisher=random.choice(publishers),
                country=random.choice(countries),
                institution=random.choice(institutions),
                subject='; '.join(random.sample(subjects, random.randint(1, 3))),
                broad_subjects=random.choice(broad_subjects),
                original_paper_date=original_date,
                original_paper_doi=f"10.1000/sample.{random.randint(1000, 9999)}.{i}",
                retraction_date=retraction_date,
                retraction_doi=f"10.1000/retraction.{random.randint(1000, 9999)}.{i}",
                reason='; '.join(random.sample(retraction_reasons, random.randint(1, 3))),
                retraction_nature=random.choice(['Retraction', 'Expression of Concern', 'Correction']),
                article_type=random.choice(article_types),
                is_open_access=random.choice([True, False]),
                paywalled=random.choice([True, False]),
            )
            
            created_papers += 1
            
            # Create citations for this paper
            num_citations = max(1, int(random.gauss(citations_per_paper, citations_per_paper * 0.3)))
            
            for j in range(num_citations):
                # Create citing paper
                citing_date = original_date + timedelta(days=random.randint(-365, 2555))  # Can cite before or after retraction
                
                citing_authors = []
                for _ in range(random.randint(1, 6)):
                    first = random.choice(first_names)
                    last = random.choice(last_names)
                    citing_authors.append(f"{first} {last}")
                
                citing_title = f"Research involving {random.choice(['analysis', 'study', 'investigation', 'examination'])} of {random.choice(['cellular', 'molecular', 'clinical', 'experimental'])} {random.choice(['mechanisms', 'pathways', 'processes', 'interactions'])}"
                
                citing_paper, created = CitingPaper.objects.get_or_create(
                    doi=f"10.1000/citing.{random.randint(1000, 9999)}.{i}.{j}",
                    defaults={
                        'openalex_id': f'citing_{random.randint(1000, 9999)}_{i}_{j}',
                        'title': citing_title,
                        'authors': '; '.join(citing_authors),
                        'journal': random.choice(journals),
                        'publication_date': citing_date,
                        'is_open_access': random.choice([True, False]),
                        'source_api': 'sample_data'
                    }
                )
                
                # Calculate days after retraction
                days_after_retraction = (citing_date - retraction_date).days
                
                Citation.objects.get_or_create(
                    retracted_paper=paper,
                    citing_paper=citing_paper,
                    defaults={
                        'citation_date': citing_date,
                        'days_after_retraction': days_after_retraction,
                        'source_api': 'sample_data'
                    }
                )
                
                created_citations += 1
        
        # Create a data import log
        DataImportLog.objects.create(
            import_type='retraction_watch',  # Use one of the valid choices
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now(),
            records_processed=created_papers,
            records_created=created_papers,
            records_updated=0,
            records_failed=0,
            status='completed',
            error_details=f'Created {created_papers} sample retracted papers with {created_citations} citations for testing'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Sample data loaded successfully!\n'
                f'📄 Created: {created_papers} retracted papers\n'
                f'📝 Created: {created_citations} citations\n'
                f'📊 Ready for testing analytics and visualizations!'
            )
        )
        
        # Print some helpful URLs
        self.stdout.write('\n🔗 Test URLs:')
        self.stdout.write(f'   Home: http://localhost:8000/')
        self.stdout.write(f'   Analytics: http://localhost:8000/analytics/')
        self.stdout.write(f'   Search: http://localhost:8000/search/')
        self.stdout.write('\n🎨 All XeraDB theme components now have data for testing!') 