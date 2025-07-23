from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from papers.models import RetractedPaper, CitingPaper, Citation, DataImportLog
from papers.utils.api_clients import CitationRetriever, OpenAlexAPI
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch citations for retracted papers from various APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--paper-id',
            type=str,
            help='Specific retracted paper record ID to fetch citations for',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of papers to process (for testing)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show what would be processed without actually fetching citations",
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help="Force refresh of citations even if recently checked",
        )
        parser.add_argument(
            '--api',
            choices=['openalex', 'semantic_scholar', 'all'],
            default='all',
            help="Which API to use for fetching citations",
        )

    def handle(self, *args, **options):
        # Create import log
        import_log = DataImportLog.objects.create(
            import_type='openalex',
            parameters=str(options)
        )
        
        try:
            self.fetch_citations(options, import_log)
            
            import_log.status = 'completed'
            import_log.end_time = timezone.now()
            import_log.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {import_log.records_processed} papers, '
                    f'created {import_log.records_created} citations, '
                    f'updated {import_log.records_updated} citations, '
                    f'failed {import_log.records_failed} papers'
                )
            )
            
        except Exception as e:
            import_log.status = 'failed'
            import_log.error_message = str(e)
            import_log.end_time = timezone.now()
            import_log.save()
            
            self.stdout.write(
                self.style.ERROR(f'Citation fetch failed: {str(e)}')
            )
            raise CommandError(f'Citation fetch failed: {str(e)}')

    def fetch_citations(self, options, import_log):
        """Fetch citations for retracted papers"""
        dry_run = options.get('dry_run', False)
        limit = options.get('limit')
        force_refresh = options.get('force_refresh', False)
        paper_id = options.get('paper_id')
        
        # Get papers to process
        queryset = RetractedPaper.objects.all()
        
        if paper_id:
            queryset = queryset.filter(record_id=paper_id)
        else:
            # Only process papers with DOIs
            queryset = queryset.filter(original_paper_doi__isnull=False)
            
            if not force_refresh:
                # Skip papers checked in the last 7 days
                from datetime import timedelta
                week_ago = timezone.now() - timedelta(days=7)
                queryset = queryset.filter(
                    Q(last_citation_check__isnull=True) |
                    Q(last_citation_check__lt=week_ago)
                )
        
        if limit:
            queryset = queryset[:limit]
        
        citation_retriever = CitationRetriever()
        openalex_api = OpenAlexAPI()
        
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_failed = 0
        
        self.stdout.write(f'Processing {queryset.count()} retracted papers...')
        
        for paper in queryset:
            try:
                if dry_run:
                    self.stdout.write(f'Would fetch citations for: {paper.title[:60]}...')
                    records_processed += 1
                    continue
                
                self.stdout.write(f'Fetching citations for: {paper.title[:60]}...')
                
                # Get citations from APIs
                use_cache = not force_refresh
                citations_data = citation_retriever.get_citations_for_paper(paper, use_cache=use_cache)
                
                citation_count = 0
                
                # Process each citing paper
                for citation_data in citations_data:
                    try:
                        # Parse the citation data using OpenAlex format
                        citing_paper_data = openalex_api.parse_work_data(citation_data)
                        
                        # Create or update citing paper
                        citing_paper, created = CitingPaper.objects.update_or_create(
                            openalex_id=citing_paper_data['openalex_id'],
                            defaults=citing_paper_data
                        )
                        
                        # Create citation link
                        citation, created = Citation.objects.get_or_create(
                            retracted_paper=paper,
                            citing_paper=citing_paper,
                            defaults={
                                'citation_date': citing_paper.publication_date,
                                'source_api': 'openalex'
                            }
                        )
                        
                        if created:
                            records_created += 1
                        else:
                            records_updated += 1
                            
                        citation_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing citation for paper {paper.record_id}: {str(e)}")
                        continue
                
                # Update paper citation count and last check time
                paper.citation_count = citation_count
                paper.last_citation_check = timezone.now()
                paper.save(update_fields=['citation_count', 'last_citation_check'])
                
                self.stdout.write(f'  Found {citation_count} citations')
                records_processed += 1
                
                # Update import log every 10 papers
                if records_processed % 10 == 0:
                    import_log.records_processed = records_processed
                    import_log.records_created = records_created
                    import_log.records_updated = records_updated
                    import_log.records_failed = records_failed
                    import_log.save()
                    self.stdout.write(f'Processed {records_processed} papers...')
                
            except Exception as e:
                records_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing paper {paper.record_id}: {str(e)}')
                )
                logger.error(f"Error processing paper {paper.record_id}: {str(e)}")
                continue
        
        # Final update of import log
        import_log.records_processed = records_processed
        import_log.records_created = records_created
        import_log.records_updated = records_updated
        import_log.records_failed = records_failed
        import_log.save() 