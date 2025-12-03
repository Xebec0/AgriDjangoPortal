"""
Management command to setup automatic backups on Windows (Task Scheduler) or Linux (cron)
"""
import os
import sys
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Setup automatic database and media backups (Windows Task Scheduler or Linux cron)"

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
            help='Show the PowerShell/cron command to create the task'
        )
        parser.add_argument(
            '--install',
            action='store_true',
            help='Automatically install the scheduled task (requires admin on Windows)'
        )
        parser.add_argument(
            '--uninstall',
            action='store_true',
            help='Remove the scheduled task'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Check if the scheduled task is installed and its status'
        )

    def handle(self, *args, **options):
        if options['test']:
            self.test_backup()
            return
        
        if options['status']:
            self.check_status()
            return
        
        if options['uninstall']:
            self.uninstall_task()
            return

        if options['show_command']:
            self.show_powershell_command(options['time'])
            return
        
        if options['install']:
            self.install_task(options['time'])
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
                # Check for manifests (new format)
                manifests = list(backup_dir.glob('backup_manifest_*.json'))
                db_backups = list(backup_dir.glob('db-*'))
                media_backups = list(backup_dir.glob('media_backup_*.zip'))
                
                if manifests or db_backups:
                    self.stdout.write(self.style.SUCCESS(f"\n✓ Backup test successful!"))
                    
                    if manifests:
                        latest_manifest = max(manifests, key=lambda p: p.stat().st_mtime)
                        self.stdout.write(f"  Latest manifest: {latest_manifest.name}")
                    
                    if db_backups:
                        latest_db = max(db_backups, key=lambda p: p.stat().st_mtime)
                        self.stdout.write(f"  Latest DB backup: {latest_db.name} ({latest_db.stat().st_size / 1024:.2f} KB)")
                    
                    if media_backups:
                        latest_media = max(media_backups, key=lambda p: p.stat().st_mtime)
                        self.stdout.write(f"  Latest media backup: {latest_media.name} ({latest_media.stat().st_size / (1024*1024):.2f} MB)")
                    
                    self.stdout.write("")
                else:
                    self.stdout.write(self.style.WARNING("\n⚠ No backup files found"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠ Backup directory not found: {backup_dir}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Backup test failed: {e}\n"))

    def check_status(self):
        """Check if the scheduled task is installed"""
        self.stdout.write(self.style.NOTICE("\nChecking backup schedule status...\n"))
        
        if sys.platform == 'win32':
            task_name = "AgriStudies DB Backup"
            try:
                result = subprocess.run(
                    ['schtasks', '/Query', '/TN', task_name, '/FO', 'LIST', '/V'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS(f"✓ Scheduled task '{task_name}' is INSTALLED\n"))
                    
                    # Parse and display key info
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if any(key in line for key in ['Status:', 'Next Run Time:', 'Last Run Time:', 'Last Result:', 'Schedule Type:']):
                            self.stdout.write(f"  {line.strip()}")
                    self.stdout.write("")
                else:
                    self.stdout.write(self.style.WARNING(f"✗ Scheduled task '{task_name}' is NOT installed"))
                    self.stdout.write("\n  Run: python manage.py setup_auto_backup --install")
                    self.stdout.write("  Or:  python manage.py setup_auto_backup (for manual instructions)\n")
                    
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR("✗ schtasks command not found"))
        else:
            # Linux - check crontab
            try:
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                if 'scheduled_backup' in result.stdout:
                    self.stdout.write(self.style.SUCCESS("✓ Cron job is INSTALLED\n"))
                    for line in result.stdout.split('\n'):
                        if 'scheduled_backup' in line:
                            self.stdout.write(f"  {line}")
                else:
                    self.stdout.write(self.style.WARNING("✗ Cron job is NOT installed"))
                    self.stdout.write("\n  Run: python manage.py crontab add\n")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error checking crontab: {e}"))

    def install_task(self, backup_time):
        """Automatically install the scheduled task"""
        if sys.platform != 'win32':
            self.stdout.write(self.style.NOTICE("Installing cron job for Linux..."))
            try:
                from django.core.management import call_command
                call_command('crontab', 'add')
                self.stdout.write(self.style.SUCCESS("\n✓ Cron jobs installed successfully!"))
                self.stdout.write("  Run 'python manage.py setup_auto_backup --status' to verify.\n")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n✗ Failed to install cron: {e}"))
            return
        
        # Windows Task Scheduler
        task_name = "AgriStudies DB Backup"
        python_path = sys.executable
        project_path = str(settings.BASE_DIR)
        
        self.stdout.write(self.style.NOTICE(f"\nInstalling Windows Task Scheduler task..."))
        self.stdout.write(f"  Task name: {task_name}")
        self.stdout.write(f"  Schedule: Daily at {backup_time}")
        self.stdout.write(f"  Python: {python_path}")
        self.stdout.write(f"  Project: {project_path}\n")
        
        # Build the schtasks command
        # Using schtasks instead of PowerShell for better compatibility
        cmd = [
            'schtasks', '/Create',
            '/TN', task_name,
            '/TR', f'"{python_path}" manage.py scheduled_backup',
            '/SC', 'DAILY',
            '/ST', backup_time,
            '/F',  # Force overwrite if exists
            '/RL', 'HIGHEST',  # Run with highest privileges
        ]
        
        try:
            # First, try without elevation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_path
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f"\n✓ Task '{task_name}' created successfully!"))
                self.stdout.write("\nTo test, run: python manage.py setup_auto_backup --test")
                self.stdout.write("To verify: python manage.py setup_auto_backup --status\n")
            else:
                # Check if it's an access denied error
                if 'Access is denied' in result.stderr or 'ERROR' in result.stderr:
                    self.stdout.write(self.style.WARNING("\n⚠ Administrator privileges required."))
                    self.stdout.write("\nPlease run one of the following as Administrator:")
                    self.stdout.write(f"\n  Option 1 (Command Prompt):")
                    self.stdout.write(f'    schtasks /Create /TN "{task_name}" /TR "\\"{python_path}\\" manage.py scheduled_backup" /SC DAILY /ST {backup_time} /F')
                    self.stdout.write(f"\n  Option 2 (PowerShell):")
                    self.show_powershell_command(backup_time)
                else:
                    self.stdout.write(self.style.ERROR(f"\n✗ Failed to create task: {result.stderr}"))
                    
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("\n✗ schtasks command not found. Are you running on Windows?"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Error: {e}"))

    def uninstall_task(self):
        """Remove the scheduled task"""
        if sys.platform != 'win32':
            self.stdout.write(self.style.NOTICE("Removing cron job..."))
            try:
                from django.core.management import call_command
                call_command('crontab', 'remove')
                self.stdout.write(self.style.SUCCESS("\n✓ Cron jobs removed successfully!\n"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n✗ Failed to remove cron: {e}"))
            return
        
        task_name = "AgriStudies DB Backup"
        self.stdout.write(self.style.NOTICE(f"\nRemoving task '{task_name}'..."))
        
        try:
            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', task_name, '/F'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f"\n✓ Task '{task_name}' removed successfully!\n"))
            else:
                if 'does not exist' in result.stderr.lower():
                    self.stdout.write(self.style.WARNING(f"\n⚠ Task '{task_name}' was not found.\n"))
                else:
                    self.stdout.write(self.style.ERROR(f"\n✗ Failed to remove task: {result.stderr}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Error: {e}"))

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
        
        self.stdout.write(self.style.WARNING("\nChoose an option:\n"))
        
        self.stdout.write(self.style.SUCCESS("Option 1: Automatic Install (Recommended)"))
        self.stdout.write("  Run as Administrator:")
        self.stdout.write(f"    python manage.py setup_auto_backup --install --time {backup_time}\n")
        
        self.stdout.write(self.style.SUCCESS("Option 2: Manual Setup via Task Scheduler GUI"))
        self.stdout.write("  1. Press Win+R, type: taskschd.msc")
        self.stdout.write("  2. Create new task with these settings:")
        self.stdout.write(f"     - Program: {python_path}")
        self.stdout.write(f"     - Arguments: manage.py scheduled_backup")
        self.stdout.write(f"     - Start in: {project_path}")
        self.stdout.write(f"     - Trigger: Daily at {backup_time}")
        self.stdout.write("  3. Enable 'Run whether user is logged on or not'")
        self.stdout.write("  4. Test: Right-click task → Run\n")
        
        self.stdout.write(self.style.SUCCESS("Option 3: PowerShell Script"))
        self.stdout.write("  Run in PowerShell (as Administrator):")
        self.stdout.write(f"    python manage.py setup_auto_backup --show-command\n")
        
        self.stdout.write(self.style.SUCCESS("Other Commands:"))
        self.stdout.write("  Check status:  python manage.py setup_auto_backup --status")
        self.stdout.write("  Test backup:   python manage.py setup_auto_backup --test")
        self.stdout.write("  Uninstall:     python manage.py setup_auto_backup --uninstall\n")
        
        self.stdout.write("="*70 + "\n")

    def show_powershell_command(self, backup_time):
        """Generate PowerShell command"""
        python_path = sys.executable
        project_path = settings.BASE_DIR
        
        ps_script = f'''
# Run this in PowerShell as Administrator
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

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily automatic database and media backup for AgriStudies"

Write-Host "Task created! Test with: Get-ScheduledTask -TaskName '$taskName' | Start-ScheduledTask"
        '''
        
        self.stdout.write(self.style.HTTP_INFO(ps_script))

    def handle_linux(self):
        """Handle Linux/Ubuntu setup"""
        self.stdout.write(self.style.NOTICE("\nDetected: Linux/Unix"))
        self.stdout.write("\nUsing django-crontab for scheduled backups.\n")
        
        try:
            from django.core.management import call_command
            
            # Show current cron jobs
            self.stdout.write(self.style.HTTP_INFO("Current cron jobs:"))
            try:
                call_command('crontab', 'show')
            except:
                self.stdout.write("  (none)")
            
            self.stdout.write(self.style.SUCCESS("\nCommands:"))
            self.stdout.write("  Install:    python manage.py crontab add")
            self.stdout.write("  Uninstall:  python manage.py crontab remove")
            self.stdout.write("  Show:       python manage.py crontab show")
            self.stdout.write("  Test:       python manage.py setup_auto_backup --test\n")
            
            self.stdout.write(self.style.HTTP_INFO("Cron schedule (from settings.py):"))
            if hasattr(settings, 'CRONJOBS'):
                for job in settings.CRONJOBS:
                    self.stdout.write(f"  {job}")
            else:
                self.stdout.write("  No CRONJOBS defined in settings.py")
            
            self.stdout.write("")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nError: {e}"))
            self.stdout.write(self.style.WARNING("\nMake sure django-crontab is installed:"))
            self.stdout.write("  pip install django-crontab\n")
