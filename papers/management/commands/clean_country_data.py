from django.core.management.base import BaseCommand
from django.db import transaction, models
from papers.models import RetractedPaper


class Command(BaseCommand):
    help = 'Clean up country data by extracting unique countries from semicolon-separated strings'

    def handle(self, *args, **options):
        self.stdout.write('Starting country data cleanup...')
        
        # Get all unique countries by splitting semicolon-separated values
        all_countries = set()
        
        papers_with_countries = RetractedPaper.objects.exclude(
            models.Q(country__isnull=True) | models.Q(country__exact='')
        )
        
        for paper in papers_with_countries:
            if paper.country:
                # Split by semicolon and clean each country
                countries = [country.strip() for country in paper.country.split(';')]
                all_countries.update(countries)
        
        # Remove empty strings and common invalid entries
        invalid_entries = {'', 'Unknown', 'unknown', 'N/A', 'n/a', 'None', 'null'}
        all_countries = all_countries - invalid_entries
        
        self.stdout.write(f'Found {len(all_countries)} unique countries')
        
        # Show sample of countries found
        self.stdout.write('\nSample countries found:')
        sample_countries = sorted(list(all_countries))[:20]
        for country in sample_countries:
            self.stdout.write(f'  - {country}')
        
        if len(all_countries) > 20:
            self.stdout.write(f'  ... and {len(all_countries) - 20} more')
        
        # Show current problematic entries
        self.stdout.write('\nCurrent problematic country entries:')
        problematic = RetractedPaper.objects.filter(
            country__icontains=';'
        ).values('country').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        for item in problematic:
            self.stdout.write(f'  "{item["country"][:100]}..." ({item["count"]} papers)')
        
        self.stdout.write(
            self.style.SUCCESS(f'Country analysis complete. Found {len(all_countries)} unique countries.')
        ) 