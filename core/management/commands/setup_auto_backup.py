"""
Management command to help setup automatic backups on Windows
"""
import os
import sys
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Setup automatic database backups for Windows Task Scheduler"

    def add_arguments(self, parser):
        parser.add_argument(
            '--time',
            type=str,
            default='17:00',
            help='Time to run backup (HH:MM format, default: 17:00)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test the backup without scheduling'
        )
        parser.add_argument(
            '--show-command',
            action='store_true',
            help='Show the PowerShell command to create the task'
        )

    def handle(self, *args, **options):
        if options['test']:
            self.test_backup()
            return

        if options['show_command']:
            self.show_powershell_command(options['time'])
            return

        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("  Automatic Backup Setup Wizard"))
        self.stdout.write("="*70 + "\n")

        # Check platform
        if sys.platform != 'win32':
            self.handle_linux()
        else:
            self.handle_windows(options['time'])

    def test_backup(self):
        """Test the backup functionality"""
        self.stdout.write(self.style.NOTICE("\nTesting backup functionality...\n"))
        
        try:
            from django.core.management import call_command
            call_command('scheduled_backup')
            
            backup_dir = settings.BASE_DIR / 'backups'
            if backup_dir.exists():
                backups = list(backup_dir.glob('db-*'))
                if backups:
                    latest = max(backups, key=lambda p: p.stat().st_mtime)
                    self.stdout.write(self.style.SUCCESS(f"\n✓ Backup test successful!"))
                    self.stdout.write(f"  Latest backup: {latest.name}")
                    self.stdout.write(f"  Size: {latest.stat().st_size / 1024:.2f} KB\n")
                else:
                    self.stdout.write(self.style.WARNING("\n⚠ No backup files found"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠ Backup directory not found: {backup_dir}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Backup test failed: {e}\n"))

    def handle_windows(self, backup_time):
        """Handle Windows setup"""
        self.stdout.write(self.style.NOTICE("\nDetected: Windows"))
        self.stdout.write("\nAutomatic backups on Windows require Windows Task Scheduler.\n")
        
        # Get paths
        python_path = sys.executable
        project_path = settings.BASE_DIR
        
        self.stdout.write(self.style.HTTP_INFO("\nCurrent Configuration:"))
        self.stdout.write(f"  Python: {python_path}")
        self.stdout.write(f"  Project: {project_path}")
        self.stdout.write(f"  Backup time: {backup_time}\n")
        
        self.stdout.write(self.style.WARNING("\nTo setup automatic backups, choose one option:\n"))
        
        self.stdout.write(self.style.SUCCESS("\nOption 1: Manual Setup (Recommended)"))
        self.stdout.write("  1. Press Win+R, type: taskschd.msc")
        self.stdout.write("  2. Create new task with these settings:")
        self.stdout.write(f"     - Program: {python_path}")
        self.stdout.write(f"     - Arguments: manage.py scheduled_backup")
        self.stdout.write(f"     - Start in: {project_path}")
        self.stdout.write(f"     - Trigger: Daily at {backup_time}")
        self.stdout.write("  3. Enable 'Run whether user is logged on or not'")
        self.stdout.write("  4. Test: Right-click task → Run\n")
        
        self.stdout.write(self.style.SUCCESS("\nOption 2: PowerShell Script (Advanced)"))
        self.stdout.write("  Run this command in PowerShell (as Administrator):\n")
        self.show_powershell_command(backup_time)
        
        self.stdout.write(self.style.SUCCESS("\n\nOption 3: Quick Test"))
        self.stdout.write("  Run this command to test backup:")
        self.stdout.write(f"  python manage.py setup_auto_backup --test\n")
        
        # Check if docs exist
        docs_path = project_path / 'docs' / 'AUTOMATIC_BACKUP_SETUP.md'
        if docs_path.exists():
            self.stdout.write(self.style.HTTP_INFO(f"\nDetailed guide: {docs_path}"))
            
        self.stdout.write("\n" + "="*70 + "\n")

    def show_powershell_command(self, backup_time):
        """Generate PowerShell command"""
        python_path = sys.executable
        project_path = settings.BASE_DIR
        
        ps_script = f'''
$taskName = "AgriStudies DB Backup"
$pythonPath = "{python_path}"
$projectPath = "{project_path}"

$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument "manage.py scheduled_backup" `
    -WorkingDirectory $projectPath

$trigger = New-ScheduledTaskTrigger -Daily -At "{backup_time}"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily automatic database backup"

Write-Host "Task created! Test it: Get-ScheduledTask -TaskName '$taskName' | Start-ScheduledTask"
        '''
        
        self.stdout.write(self.style.HTTP_INFO(ps_script))

    def handle_linux(self):
        """Handle Linux/Ubuntu setup"""
        self.stdout.write(self.style.NOTICE("\nDetected: Linux/Unix"))
        self.stdout.write("\nSetting up automatic backups using django-crontab...\n")
        
        try:
            from django.core.management import call_command
            
            # Show current cron jobs
            self.stdout.write(self.style.HTTP_INFO("Current cron jobs:"))
            call_command('crontab', 'show')
            
            # Ask to install
            self.stdout.write(self.style.SUCCESS("\nTo install cron jobs, run:"))
            self.stdout.write("  python manage.py crontab add")
            self.stdout.write("\nTo remove cron jobs, run:")
            self.stdout.write("  python manage.py crontab remove\n")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nError: {e}"))
            self.stdout.write(self.style.WARNING("\nMake sure django-crontab is installed:"))
            self.stdout.write("  pip install django-crontab\n")
