from django.core.management.base import BaseCommand
from django.db.models import Q
from papers.models import Citation
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix days_after_retraction calculation for all citations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of citations to process per batch (default: 1000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        self.stdout.write("Starting citation date fix...")
        
        # Find citations that need fixing
        citations_to_fix = Citation.objects.filter(
            Q(days_after_retraction__isnull=True)
        ).select_related('retracted_paper', 'citing_paper')
        
        total_count = citations_to_fix.count()
        self.stdout.write(f"Found {total_count:,} citations to fix")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            
            # Show sample of what would be fixed
            sample = citations_to_fix[:5]
            for citation in sample:
                if (citation.retracted_paper.retraction_date and 
                    citation.citing_paper and 
                    citation.citing_paper.publication_date):
                    
                    days_diff = (citation.citing_paper.publication_date - 
                               citation.retracted_paper.retraction_date).days
                    
                    self.stdout.write(
                        f"Citation {citation.id}: would set days_after_retraction = {days_diff}"
                    )
            return
        
        # Process in batches using bulk updates
        fixed_count = 0
        batch_count = 0
        citations_batch = []
        
        # Use iterator to avoid loading all objects into memory
        for citation in citations_to_fix.iterator(chunk_size=batch_size):
            if (citation.retracted_paper.retraction_date and 
                citation.citing_paper and 
                citation.citing_paper.publication_date):
                
                # Calculate days after retraction (can be negative)
                days_diff = (citation.citing_paper.publication_date - 
                           citation.retracted_paper.retraction_date).days
                
                citation.days_after_retraction = days_diff
                citations_batch.append(citation)
                
                if len(citations_batch) >= batch_size:
                    # Bulk update
                    Citation.objects.bulk_update(citations_batch, ['days_after_retraction'])
                    fixed_count += len(citations_batch)
                    batch_count += 1
                    self.stdout.write(f"Processed batch {batch_count}: {fixed_count:,} citations fixed")
                    citations_batch = []
        
        # Update remaining citations in final batch
        if citations_batch:
            Citation.objects.bulk_update(citations_batch, ['days_after_retraction'])
            fixed_count += len(citations_batch)
            batch_count += 1
            self.stdout.write(f"Processed final batch {batch_count}: {fixed_count:,} citations fixed")
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully fixed {fixed_count:,} citations out of {total_count:,}")
        )
        
        # Show post-retraction statistics
        post_retraction_count = Citation.objects.filter(days_after_retraction__gt=0).count()
        pre_retraction_count = Citation.objects.filter(days_after_retraction__lt=0).count()
        same_day_count = Citation.objects.filter(days_after_retraction=0).count()
        
        self.stdout.write("\n=== CITATION STATISTICS ===")
        self.stdout.write(f"Post-retraction citations: {post_retraction_count:,}")
        self.stdout.write(f"Pre-retraction citations: {pre_retraction_count:,}")
        self.stdout.write(f"Same-day citations: {same_day_count:,}")
        self.stdout.write(f"Total with dates: {post_retraction_count + pre_retraction_count + same_day_count:,}") 