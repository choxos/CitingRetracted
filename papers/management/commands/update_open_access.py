from django.core.management.base import BaseCommand
from django.db.models import Q
from papers.models import RetractedPaper


class Command(BaseCommand):
    help = 'Update open access status for papers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-true',
            action='store_true',
            help='Set all papers to open access',
        )
        parser.add_argument(
            '--all-false',
            action='store_true',
            help='Set all papers to NOT open access',
        )
        parser.add_argument(
            '--recent',
            type=int,
            help='Set last N papers to open access',
        )
        parser.add_argument(
            '--record-ids',
            nargs='+',
            help='List of record IDs to set as open access',
        )
        parser.add_argument(
            '--journal',
            type=str,
            help='Set all papers from a specific journal to open access',
        )
        parser.add_argument(
            '--set-false',
            action='store_true',
            help='Set the selected papers to NOT open access instead of open access',
        )

    def handle(self, *args, **options):
        updated_count = 0
        is_open_access = not options['set_false']  # Default to True unless --set-false is used
        
        status_text = "open access" if is_open_access else "NOT open access"
        
        if options['all_true']:
            if not is_open_access:
                self.stdout.write(self.style.ERROR("Cannot use --all-true with --set-false"))
                return
            updated_count = RetractedPaper.objects.update(is_open_access=True)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set all {updated_count} papers to open access')
            )
            
        elif options['all_false']:
            if is_open_access:
                self.stdout.write(self.style.ERROR("Cannot use --all-false without --set-false"))
                return
            updated_count = RetractedPaper.objects.update(is_open_access=False)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set all {updated_count} papers to NOT open access')
            )
            
        elif options['recent']:
            recent_papers = RetractedPaper.objects.order_by('-created_at')[:options['recent']]
            record_ids = [paper.record_id for paper in recent_papers]
            updated_count = RetractedPaper.objects.filter(record_id__in=record_ids).update(
                is_open_access=is_open_access
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {updated_count} recent papers to {status_text}')
            )
            
        elif options['record_ids']:
            updated_count = RetractedPaper.objects.filter(
                record_id__in=options['record_ids']
            ).update(is_open_access=is_open_access)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {updated_count} papers to {status_text}')
            )
            
        elif options['journal']:
            updated_count = RetractedPaper.objects.filter(
                journal__icontains=options['journal']
            ).update(is_open_access=is_open_access)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {updated_count} papers from "{options["journal"]}" to {status_text}')
            )
            
        else:
            self.stdout.write(
                self.style.ERROR('Please specify one of: --all-true, --all-false, --recent N, --record-ids [...], or --journal "name"')
            )
            return

        # Show current distribution
        total_papers = RetractedPaper.objects.count()
        open_access_count = RetractedPaper.objects.filter(is_open_access=True).count()
        not_open_access_count = total_papers - open_access_count
        
        self.stdout.write(f'\nCurrent distribution:')
        self.stdout.write(f'  Open access: {open_access_count} papers ({open_access_count/total_papers*100:.1f}%)')
        self.stdout.write(f'  Not open access: {not_open_access_count} papers ({not_open_access_count/total_papers*100:.1f}%)')