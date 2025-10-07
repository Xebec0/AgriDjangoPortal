"""
Management command to warm up the cache with frequently accessed data
Usage: python manage.py warm_cache
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.cache_utils import warm_cache


class Command(BaseCommand):
    help = 'Warm up the cache with frequently accessed data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Clear cache before warming',
        )

    def handle(self, *args, **options):
        if options['clear_first']:
            self.stdout.write('Clearing cache...')
            cache.clear()

        self.stdout.write('Warming up cache...')
        
        try:
            warm_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully warmed up cache')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error warming cache: {e}')
            )
