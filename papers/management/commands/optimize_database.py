from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Optimize database with indexes and performance improvements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run ANALYZE on tables after creating indexes'
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM on tables for PostgreSQL optimization'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting database optimization...')
        )
        
        # Create performance indexes
        self.create_performance_indexes()
        
        # Create composite indexes for common queries
        self.create_composite_indexes()
        
        # Create text search indexes
        self.create_text_search_indexes()
        
        if options['analyze']:
            self.analyze_tables()
        
        if options['vacuum']:
            self.vacuum_tables()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Database optimization completed!')
        )

    def create_performance_indexes(self):
        """Create indexes for improved query performance"""
        self.stdout.write('📊 Creating performance indexes...')
        
        indexes = [
            # RetractedPaper indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_retraction_date ON retracted_papers(retraction_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_original_date ON retracted_papers(original_paper_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_citation_count ON retracted_papers(citation_count DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_journal ON retracted_papers(journal);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_country ON retracted_papers(country);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_publisher ON retracted_papers(publisher);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_is_open_access ON retracted_papers(is_open_access);",
            
            # Citation indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_date ON citing_papers(publication_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_days_after ON citations(days_after_retraction);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_retracted_paper ON citations(retracted_paper_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_citing_paper ON citations(citing_paper_id);",
            
            # CitingPaper indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_paper_journal ON citing_papers(journal);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_paper_publication_year ON citing_papers(publication_year DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_paper_is_open_access ON citing_papers(is_open_access);",
        ]
        
        with connection.cursor() as cursor:
            for index_sql in indexes:
                try:
                    self.stdout.write(f'   Creating index: {index_sql.split("IF NOT EXISTS")[1].split("ON")[0].strip()}')
                    cursor.execute(index_sql)
                    self.stdout.write(self.style.SUCCESS('   ✅ Created'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ Skipped (may already exist): {str(e)}'))

    def create_composite_indexes(self):
        """Create composite indexes for common query patterns"""
        self.stdout.write('🔗 Creating composite indexes...')
        
        composite_indexes = [
            # Analytics queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_date_journal ON retracted_papers(retraction_date DESC, journal);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_country_date ON retracted_papers(country, retraction_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_subject_date ON retracted_papers(subject, retraction_date DESC);",
            
            # Citation analysis
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_paper_days ON citations(retracted_paper_id, days_after_retraction);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citation_date_days ON citations(citation_date DESC, days_after_retraction);",
            
            # Search optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_journal_date ON retracted_papers(journal, retraction_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_paper_journal_date ON citing_papers(journal, publication_date DESC);",
        ]
        
        with connection.cursor() as cursor:
            for index_sql in composite_indexes:
                try:
                    self.stdout.write(f'   Creating composite index: {index_sql.split("IF NOT EXISTS")[1].split("ON")[0].strip()}')
                    cursor.execute(index_sql)
                    self.stdout.write(self.style.SUCCESS('   ✅ Created'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ Skipped: {str(e)}'))

    def create_text_search_indexes(self):
        """Create full-text search indexes for better search performance"""
        self.stdout.write('🔍 Creating text search indexes...')
        
        # Only create these for PostgreSQL
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            text_indexes = [
                # Full-text search indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_title_gin ON retracted_papers USING gin(to_tsvector('english', title));",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_author_gin ON retracted_papers USING gin(to_tsvector('english', author));",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_abstract_gin ON retracted_papers USING gin(to_tsvector('english', COALESCE(abstract, '')));",
                
                # Trigram indexes for fuzzy search
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_title_trgm ON retracted_papers USING gin(title gin_trgm_ops);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retracted_paper_journal_trgm ON retracted_papers USING gin(journal gin_trgm_ops);",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citing_paper_title_trgm ON citing_papers USING gin(title gin_trgm_ops);",
            ]
            
            with connection.cursor() as cursor:
                for index_sql in text_indexes:
                    try:
                        if 'CREATE EXTENSION' in index_sql:
                            self.stdout.write('   Creating extension: pg_trgm')
                        else:
                            self.stdout.write(f'   Creating text search index: {index_sql.split("IF NOT EXISTS")[1].split("ON")[0].strip()}')
                        cursor.execute(index_sql)
                        self.stdout.write(self.style.SUCCESS('   ✅ Created'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Skipped: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('   Text search indexes only supported on PostgreSQL'))

    def analyze_tables(self):
        """Run ANALYZE to update table statistics"""
        self.stdout.write('📈 Running ANALYZE on tables...')
        
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            tables = ['retracted_papers', 'citations', 'citing_papers', 'data_import_logs']
            
            with connection.cursor() as cursor:
                for table in tables:
                    try:
                        self.stdout.write(f'   Analyzing table: {table}')
                        cursor.execute(f'ANALYZE {table};')
                        self.stdout.write(self.style.SUCCESS('   ✅ Analyzed'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ❌ Failed: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('   ANALYZE only supported on PostgreSQL'))

    def vacuum_tables(self):
        """Run VACUUM to reclaim space and update statistics"""
        self.stdout.write('🧹 Running VACUUM on tables...')
        
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            tables = ['retracted_papers', 'citations', 'citing_papers', 'data_import_logs']
            
            with connection.cursor() as cursor:
                for table in tables:
                    try:
                        self.stdout.write(f'   Vacuuming table: {table}')
                        cursor.execute(f'VACUUM ANALYZE {table};')
                        self.stdout.write(self.style.SUCCESS('   ✅ Vacuumed'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ❌ Failed: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('   VACUUM only supported on PostgreSQL'))

    def get_index_usage_stats(self):
        """Display index usage statistics (PostgreSQL only)"""
        self.stdout.write('📊 Index usage statistics:')
        
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_tup_read DESC;
                """)
                
                results = cursor.fetchall()
                for row in results:
                    self.stdout.write(f'   {row[1]}.{row[2]}: {row[3]} reads, {row[4]} fetches')
        else:
            self.stdout.write(self.style.WARNING('   Index stats only available on PostgreSQL')) 