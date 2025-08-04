"""
Management command to diagnose impossible retraction rates (>100%).

This command investigates countries with retraction rates over 100% to identify
data quality issues and their root causes.

Usage:
    python manage.py diagnose_retraction_rates
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Sum, Count, Min, Max
from papers.models import DemocracyData


class Command(BaseCommand):
    help = 'Diagnose impossible retraction rates and identify data quality issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RETRACTION RATE DIAGNOSTIC REPORT ===\n'))
        
        # Get aggregated data same as the view
        country_data = DemocracyData.objects.values('country', 'iso3', 'region').annotate(
            avg_democracy=Avg('democracy'),
            total_retractions=Sum('retractions'),
            total_publications=Sum('publications'),
            num_years=Count('year'),
            min_year=Min('year'),
            max_year=Max('year')
        ).filter(
            avg_democracy__isnull=False,
            total_publications__gt=0
        ).order_by('-total_publications')
        
        total_countries = len(country_data)
        impossible_rates = []
        
        self.stdout.write(f"📊 ANALYZING {total_countries} COUNTRIES...\n")
        
        for item in country_data:
            retraction_rate = (item['total_retractions'] or 0) / item['total_publications']
            
            if retraction_rate > 1.0:  # Over 100%
                impossible_rates.append({
                    'country': item['country'],
                    'iso3': item['iso3'],
                    'region': item['region'],
                    'retractions': item['total_retractions'],
                    'publications': item['total_publications'],
                    'rate': retraction_rate,
                    'years': item['num_years'],
                    'year_range': f"{item['min_year']}-{item['max_year']}"
                })
        
        # Report findings
        if not impossible_rates:
            self.stdout.write(self.style.SUCCESS("✅ NO IMPOSSIBLE RETRACTION RATES FOUND!"))
            return
            
        self.stdout.write(self.style.ERROR(f"🚨 FOUND {len(impossible_rates)} COUNTRIES WITH IMPOSSIBLE RATES:\n"))
        
        # Sort by worst rates first
        impossible_rates.sort(key=lambda x: x['rate'], reverse=True)
        
        for item in impossible_rates[:10]:  # Show top 10 worst
            self.stdout.write(
                f"❌ {item['country']} ({item['iso3']}): "
                f"{item['rate']*100:.1f}% "
                f"({item['retractions']} retractions / {item['publications']} publications)"
            )
            self.stdout.write(f"   📅 Years: {item['year_range']} ({item['years']} observations)")
            self.stdout.write(f"   🌍 Region: {item['region']}\n")
        
        if len(impossible_rates) > 10:
            self.stdout.write(f"... and {len(impossible_rates) - 10} more countries\n")
        
        # Investigate specific country in detail
        worst_country = impossible_rates[0]
        self.stdout.write(self.style.WARNING(f"🔍 DETAILED ANALYSIS: {worst_country['country']}\n"))
        
        detailed_data = DemocracyData.objects.filter(
            country=worst_country['country']
        ).order_by('year')
        
        self.stdout.write("Year-by-year breakdown:")
        total_ret = 0
        total_pub = 0
        
        for record in detailed_data:
            rate = (record.retractions / record.publications * 100) if record.publications > 0 else 0
            self.stdout.write(
                f"  {record.year}: {record.retractions} ret / {record.publications} pub = {rate:.1f}%"
            )
            total_ret += record.retractions
            total_pub += record.publications
        
        self.stdout.write(f"\nTOTALS: {total_ret} retractions / {total_pub} publications = {(total_ret/total_pub)*100:.1f}%")
        
        # Suggestions
        self.stdout.write(self.style.SUCCESS('\n🔧 RECOMMENDATIONS:'))
        self.stdout.write('1. CHECK DATA SOURCE: Verify retraction vs publication definitions')
        self.stdout.write('2. INVESTIGATE AGGREGATION: May be summing across wrong dimensions')
        self.stdout.write('3. DATA VALIDATION: Add constraints to prevent impossible values')
        self.stdout.write('4. CAPPING: Limit display to 100% max for visualization')
        self.stdout.write('5. FLAGGING: Mark problematic countries for manual review')
        
        # Summary statistics
        avg_impossible_rate = sum(item['rate'] for item in impossible_rates) / len(impossible_rates)
        max_rate = max(item['rate'] for item in impossible_rates)
        
        self.stdout.write(f'\n📈 STATISTICS:')
        self.stdout.write(f'   Countries affected: {len(impossible_rates)} / {total_countries} ({len(impossible_rates)/total_countries*100:.1f}%)')
        self.stdout.write(f'   Average impossible rate: {avg_impossible_rate*100:.1f}%')
        self.stdout.write(f'   Maximum rate found: {max_rate*100:.1f}%')