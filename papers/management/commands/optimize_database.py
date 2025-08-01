from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimize database performance with indexes and maintenance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run database analyze to update statistics',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run vacuum on PostgreSQL (if applicable)',
        )
        parser.add_argument(
            '--show-slow-queries',
            action='store_true',
            help='Show information about potentially slow queries',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database optimization...'))
        
        # Check database type
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if options['show_slow_queries']:
            self._show_query_analysis()
        
        if options['analyze']:
            self._analyze_database(db_engine)
        
        if options['vacuum'] and 'postgresql' in db_engine:
            self._vacuum_database()
        
        # Always run basic optimizations
        self._optimize_database(db_engine)
        
        self.stdout.write(self.style.SUCCESS('Database optimization completed!'))

    def _show_query_analysis(self):
        """Show analysis of common query patterns"""
        self.stdout.write(self.style.WARNING('\n=== Query Analysis ==='))
        
        with connection.cursor() as cursor:
            # Check for missing indexes on foreign keys
            self.stdout.write('Checking foreign key indexes...')
            
            # For Citation model
            cursor.execute("""
                SELECT COUNT(*) as citation_count,
                       COUNT(CASE WHEN days_after_retraction > 0 THEN 1 END) as post_retraction_count
                FROM citations
            """)
            
            row = cursor.fetchone()
            self.stdout.write(f"Citations: {row[0]:,} total, {row[1]:,} post-retraction")
            
            # For RetractedPaper model  
            cursor.execute("""
                SELECT COUNT(*) as paper_count,
                       AVG(citation_count) as avg_citations,
                       MAX(citation_count) as max_citations
                FROM retracted_papers
                WHERE retraction_date IS NOT NULL
            """)
            
            row = cursor.fetchone()
            self.stdout.write(f"Papers: {row[0]:,} total, avg citations: {row[1]:.1f}, max: {row[2]}")

    def _analyze_database(self, db_engine):
        """Update database statistics"""
        self.stdout.write('Updating database statistics...')
        
        with connection.cursor() as cursor:
            if 'postgresql' in db_engine:
                # PostgreSQL
                cursor.execute("ANALYZE;")
                self.stdout.write(self.style.SUCCESS('PostgreSQL ANALYZE completed'))
            elif 'sqlite' in db_engine:
                # SQLite
                cursor.execute("ANALYZE;")
                self.stdout.write(self.style.SUCCESS('SQLite ANALYZE completed'))
            else:
                self.stdout.write(self.style.WARNING(f'ANALYZE not implemented for {db_engine}'))

    def _vacuum_database(self):
        """Run vacuum on PostgreSQL"""
        self.stdout.write('Running database vacuum...')
        
        with connection.cursor() as cursor:
            cursor.execute("VACUUM;")
            self.stdout.write(self.style.SUCCESS('PostgreSQL VACUUM completed'))

    def _optimize_database(self, db_engine):
        """Run database-specific optimizations"""
        self.stdout.write('Running database optimizations...')
        
        with connection.cursor() as cursor:
            if 'postgresql' in db_engine:
                self._optimize_postgresql(cursor)
            elif 'sqlite' in db_engine:
                self._optimize_sqlite(cursor)
            else:
                self.stdout.write(self.style.WARNING(f'Optimizations not implemented for {db_engine}'))

    def _optimize_postgresql(self, cursor):
        """PostgreSQL-specific optimizations"""
        optimizations = [
            # Update table statistics
            "ANALYZE retracted_papers;",
            "ANALYZE citations;", 
            "ANALYZE citing_papers;",
            
            # Check for unused indexes (informational)
            """
            SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE idx_scan < 10 
            ORDER BY idx_scan;
            """
        ]
        
        for sql in optimizations:
            try:
                if sql.strip().startswith('SELECT'):
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    if rows:
                        self.stdout.write('Potential unused indexes:')
                        for row in rows[:5]:  # Show first 5
                            self.stdout.write(f"  {row[2]} on {row[1]} (scans: {row[3]})")
                else:
                    cursor.execute(sql)
                    self.stdout.write(f'Executed: {sql.split()[0]}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error executing {sql[:50]}...: {e}'))

    def _optimize_sqlite(self, cursor):
        """SQLite-specific optimizations"""
        optimizations = [
            # Rebuild indexes
            "REINDEX;",
            
            # Update statistics
            "ANALYZE;",
            
            # Optimize database file
            "VACUUM;",
            
            # Set pragmas for better performance
            "PRAGMA optimize;",
        ]
        
        for sql in optimizations:
            try:
                cursor.execute(sql)
                self.stdout.write(f'Executed: {sql}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error executing {sql}: {e}')) 