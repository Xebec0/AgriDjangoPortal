"""
Management command to clear cache
Usage: python manage.py clear_cache
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.cache_utils import invalidate_program_cache, invalidate_candidate_cache


class Command(BaseCommand):
    help = 'Clear cache entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['all', 'programs', 'candidates'],
            default='all',
            help='Type of cache to clear',
        )

    def handle(self, *args, **options):
        cache_type = options['type']
        
        if cache_type == 'all':
            self.stdout.write('Clearing all cache...')
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all cache')
            )
        elif cache_type == 'programs':
            self.stdout.write('Clearing program cache...')
            invalidate_program_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared program cache')
            )
        elif cache_type == 'candidates':
            self.stdout.write('Clearing candidate cache...')
            invalidate_candidate_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared candidate cache')
            )
