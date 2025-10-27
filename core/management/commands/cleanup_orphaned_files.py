"""
Management command to clean up orphaned file records.
Usage: python manage.py cleanup_orphaned_files
"""
from django.core.management.base import BaseCommand
from core.models import UploadedFile


class Command(BaseCommand):
    help = 'Clean up UploadedFile records for files that no longer exist in storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write('Scanning for orphaned file records...')

        # Get all active file records
        active_records = UploadedFile.objects.filter(is_active=True)
        total = active_records.count()
        orphaned = 0

        self.stdout.write(f'Found {total} active file records to check')

        from django.conf import settings
        import os

        for record in active_records:
            file_path = os.path.join(settings.MEDIA_ROOT, record.file_path)

            if not os.path.exists(file_path):
                orphaned += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Orphaned: {record.file_name} (User: {record.user.username}, '
                        f'Type: {record.get_document_type_display()})'
                    )
                )

                if not dry_run:
                    record.is_active = False
                    record.save()
                    self.stdout.write(self.style.SUCCESS(f'  → Marked as inactive'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN COMPLETE: Found {orphaned} orphaned records (out of {total} total)'
                )
            )
            self.stdout.write('Run without --dry-run to actually clean them up')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCLEANUP COMPLETE: Marked {orphaned} orphaned records as inactive (out of {total} total)'
                )
            )

        # Show summary
        if orphaned == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ All file records are valid!'))
        else:
            percentage = (orphaned / total * 100) if total > 0 else 0
            self.stdout.write(f'\nOrphaned records: {orphaned}/{total} ({percentage:.1f}%)')
