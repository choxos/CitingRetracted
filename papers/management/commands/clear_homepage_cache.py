from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear homepage and analytics cache to refresh top subjects and institutions'

    def handle(self, *args, **options):
        cache_keys = [
            'home_stats_v1',
            'home_sidebar_stats_v1',
            'home_top_problematic_v1',
            'analytics_complex_data_v2',
            'analytics_basic_stats_v2',
            'analytics_overview',
            'retraction_trends',
            'citation_analysis',
            'subject_analysis'
        ]
        
        cleared_count = 0
        
        for key in cache_keys:
            if cache.get(key) is not None:
                cache.delete(key)
                cleared_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cleared cache key: {key}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Cache key not found: {key}')
                )
        
        # Clear all cache keys with prefix patterns
        try:
            # For Redis-based cache, clear pattern-based keys
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('🧹 Cleared all cache entries')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Could not clear all cache: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎯 Cache clearing complete! Cleared {cleared_count} specific keys.\n'
                f'📊 Homepage and analytics will now show updated top subjects and institutions.\n'
                f'🔄 Please refresh your browser to see the changes.'
            )
        ) 