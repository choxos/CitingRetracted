from django.core.management.base import BaseCommand
from django.db import transaction, models
from papers.models import RetractedPaper


class Command(BaseCommand):
    help = 'Clean up institution names by replacing unknown/unavailable variants with NA'

    def handle(self, *args, **options):
        self.stdout.write('Starting institution name cleanup...')
        
        # List of variations that should be replaced with "NA"
        unknown_variations = [
            'Unknown',
            'unknown', 
            'UNKNOWN',
            'unavailable',
            'Unavailable',
            'UNAVAILABLE',
            'N/A',
            'n/a',
            'null',
            'NULL',
            'None',
            'none',
            '',  # empty string
        ]
        
        total_updated = 0
        
        with transaction.atomic():
            for variation in unknown_variations:
                if variation == '':
                    # Handle empty strings and None values
                    updated = RetractedPaper.objects.filter(
                        institution__isnull=True
                    ).update(institution='NA')
                    if updated > 0:
                        self.stdout.write(f'Updated {updated} NULL institutions to "NA"')
                        total_updated += updated
                    
                    updated = RetractedPaper.objects.filter(
                        institution__exact=''
                    ).update(institution='NA')
                    if updated > 0:
                        self.stdout.write(f'Updated {updated} empty string institutions to "NA"')
                        total_updated += updated
                else:
                    # Handle specific text variations
                    updated = RetractedPaper.objects.filter(
                        institution__exact=variation
                    ).update(institution='NA')
                    if updated > 0:
                        self.stdout.write(f'Updated {updated} "{variation}" institutions to "NA"')
                        total_updated += updated
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {total_updated} institution records to "NA"')
        )
        
        # Show current institution stats
        self.stdout.write('\nCurrent top institutions:')
        top_institutions = RetractedPaper.objects.values('institution').annotate(
            count=models.Count('id')
        ).exclude(institution__isnull=True).order_by('-count')[:10]
        
        for inst in top_institutions:
            self.stdout.write(f'  {inst["institution"]}: {inst["count"]}') 