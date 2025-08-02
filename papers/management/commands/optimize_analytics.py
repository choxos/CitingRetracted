from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimize database indexes for analytics performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze current index usage',
        )
        parser.add_argument(
            '--optimize',
            action='store_true', 
            help='Create recommended indexes',
        )

    def handle(self, *args, **options):
        if options['analyze']:
            self.analyze_indexes()
        
        if options['optimize']:
            self.optimize_indexes()

    def analyze_indexes(self):
        """Analyze current index usage for analytics queries"""
        self.stdout.write("Analyzing current database indexes for analytics...")
        
        with connection.cursor() as cursor:
            # Check if we're using PostgreSQL
            if 'postgresql' in connection.settings_dict['ENGINE']:
                # PostgreSQL specific analysis
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('papers_retractedpaper', 'papers_citation', 'papers_citingpaper')
                    ORDER BY idx_scan DESC;
                """)
                
                results = cursor.fetchall()
                self.stdout.write("\nCurrent index usage:")
                for row in results:
                    self.stdout.write(f"  {row[2]}: {row[3]} scans, {row[4]} tuples read")
            
            # Check for missing indexes on commonly queried fields
            self.stdout.write("\nRecommended indexes for analytics queries:")
            self.stdout.write("  1. retraction_nature + retraction_date (compound)")
            self.stdout.write("  2. retraction_nature + citation_count (compound)")
            self.stdout.write("  3. days_after_retraction (citations table)")
            self.stdout.write("  4. publication_date (citing papers)")
            self.stdout.write("  5. journal (retracted papers)")
            self.stdout.write("  6. country (retracted papers)")
            self.stdout.write("  7. subject (retracted papers)")

    def optimize_indexes(self):
        """Create optimized indexes for analytics performance"""
        self.stdout.write("Creating optimized indexes for analytics...")
        
        indexes = [
            # Compound indexes for common analytics filters
            {
                'name': 'idx_retracted_papers_nature_date',
                'table': 'papers_retractedpaper',
                'fields': 'retraction_nature, retraction_date',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_papers_nature_date ON papers_retractedpaper (retraction_nature, retraction_date) WHERE retraction_nature IS NOT NULL AND retraction_date IS NOT NULL;'
            },
            {
                'name': 'idx_retracted_papers_nature_citations',
                'table': 'papers_retractedpaper', 
                'fields': 'retraction_nature, citation_count',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_papers_nature_citations ON papers_retractedpaper (retraction_nature, citation_count) WHERE retraction_nature IS NOT NULL AND citation_count IS NOT NULL;'
            },
            {
                'name': 'idx_citations_days_after',
                'table': 'papers_citation',
                'fields': 'days_after_retraction',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citations_days_after ON papers_citation (days_after_retraction) WHERE days_after_retraction IS NOT NULL;'
            },
            {
                'name': 'idx_citing_papers_pub_date',
                'table': 'papers_citingpaper',
                'fields': 'publication_date',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_papers_pub_date ON papers_citingpaper (publication_date) WHERE publication_date IS NOT NULL;'
            },
            {
                'name': 'idx_retracted_papers_journal',
                'table': 'papers_retractedpaper',
                'fields': 'journal',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_papers_journal ON papers_retractedpaper (journal) WHERE journal IS NOT NULL AND journal != \'\';'
            },
            {
                'name': 'idx_retracted_papers_country',
                'table': 'papers_retractedpaper',
                'fields': 'country', 
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_papers_country ON papers_retractedpaper (country) WHERE country IS NOT NULL AND country != \'\';'
            },
            {
                'name': 'idx_retracted_papers_subject',
                'table': 'papers_retractedpaper',
                'fields': 'subject',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_papers_subject ON papers_retractedpaper (subject) WHERE subject IS NOT NULL AND subject != \'\';'
            }
        ]

        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    self.stdout.write(f"Creating index: {index['name']} on {index['table']}({index['fields']})")
                    cursor.execute(index['sql'])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Created {index['name']}"))
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(self.style.WARNING(f"  - Index {index['name']} already exists"))
                    else:
                        self.stdout.write(self.style.ERROR(f"  ✗ Failed to create {index['name']}: {e}"))

        self.stdout.write("\nOptimization complete!")
        self.stdout.write("Note: Indexes are created CONCURRENTLY to avoid blocking production queries.")
        self.stdout.write("You can analyze the impact with: python manage.py optimize_analytics --analyze") 