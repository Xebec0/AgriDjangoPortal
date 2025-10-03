# Automatic Database Backup Setup Guide

## Overview

The system has automatic backup functionality built-in, but it requires **one-time setup** to activate scheduled backups.

## Current Status

- ✅ Backup commands are configured
- ✅ Backup rotation is enabled (keeps 7 days by default)
- ✅ Activity logging is working
- ⚠️ **Automatic scheduling needs activation**

---

## Quick Setup (Choose Your Platform)

### For Windows (Recommended for Local Development)

#### Option 1: Windows Task Scheduler (GUI Method)

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**:
   - Click "Create Task" (not "Create Basic Task")
   - Name: `AgriStudies DB Backup`
   - Description: `Daily automatic database backup`
   - Check: "Run whether user is logged on or not"
   - Check: "Run with highest privileges"

3. **Set Trigger**:
   - Go to "Triggers" tab → "New"
   - Begin the task: "On a schedule"
   - Settings: Daily
   - Start time: 17:00:00 (5:00 PM)
   - Check: "Enabled"
   - Click "OK"

4. **Set Action**:
   - Go to "Actions" tab → "New"
   - Action: "Start a program"
   - Program/script: `python.exe` (or full path: `C:\Users\PC\AppData\Local\Programs\Python\Python313\python.exe`)
   - Add arguments: `manage.py scheduled_backup`
   - Start in: `C:\Users\PC\Documents\GitHub\AgriDjangoPortal`
   - Click "OK"

5. **Configure Settings**:
   - Go to "Settings" tab
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after a scheduled start is missed"
   - If the task fails, restart: Every 1 hour
   - Attempt to restart up to: 3 times
   - Click "OK"

6. **Test the Task**:
   - Right-click on your task → "Run"
   - Check `C:\Users\PC\Documents\GitHub\AgriDjangoPortal\backups` for new backup file

#### Option 2: PowerShell Script (Automated)

Create a file `setup_backup_task.ps1` with this content:

```powershell
# Run as Administrator

$taskName = "AgriStudies DB Backup"
$pythonPath = "python.exe"  # Or full path to python
$projectPath = "C:\Users\PC\Documents\GitHub\AgriDjangoPortal"
$scriptPath = "$projectPath\manage.py"

# Create the task action
$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument "manage.py scheduled_backup" `
    -WorkingDirectory $projectPath

# Create the trigger (daily at 5:00 PM)
$trigger = New-ScheduledTaskTrigger -Daily -At "17:00"

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 60) `
    -RestartCount 3

# Register the task
Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily automatic database backup for AgriStudies"

Write-Host "Task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "Backups will run daily at 5:00 PM" -ForegroundColor Green
```

Then run:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_backup_task.ps1
```

---

### For Linux/Ubuntu (Production Servers)

#### Step 1: Install Cron Jobs

```bash
# Navigate to project directory
cd /path/to/AgriDjangoPortal

# Activate virtual environment
source venv/bin/activate

# Add cron jobs to system crontab
python manage.py crontab add

# Verify cron jobs are installed
python manage.py crontab show
```

#### Step 2: Check Cron Status

```bash
# List all cron jobs
python manage.py crontab show

# Remove cron jobs (if needed)
python manage.py crontab remove

# Re-add cron jobs
python manage.py crontab add
```

---

## Manual Backup Commands

### Run Backup Manually

```bash
# Basic backup
python manage.py backup_db

# Custom output directory
python manage.py backup_db --output-dir=/path/to/backups

# Keep backups for 14 days instead of 7
python manage.py backup_db --keep-days=14
```

### Run Scheduled Backup (With Notifications)

```bash
python manage.py scheduled_backup
```

This will:
- Run the backup
- Create notifications for admins
- Log to ActivityLog
- Show in admin panel

---

## Backup Configuration

### Current Settings (in `settings.py`)

```python
CRONJOBS = [
    # Run backup at 5:00 PM (17:00) every day
    ('0 17 * * *', 'django.core.management.call_command', ['scheduled_backup']),
]
```

### Customize Backup Schedule

Edit `agrostudies_project/settings.py`:

```python
CRONJOBS = [
    # Format: ('minute hour day month day_of_week', 'command', [args])
    
    # Every day at 5:00 PM
    ('0 17 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Every 6 hours
    # ('0 */6 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Twice a day (8 AM and 8 PM)
    # ('0 8,20 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Every Sunday at midnight
    # ('0 0 * * 0', 'django.core.management.call_command', ['scheduled_backup']),
]
```

After changing, **re-install the cron job** (Linux only):
```bash
python manage.py crontab remove
python manage.py crontab add
```

---

## Backup Location

**Default**: `C:\Users\PC\Documents\GitHub\AgriDjangoPortal\backups`

**Files Created**:
- SQLite: `db-sqlite-YYYYMMDD-HHMMSS.sqlite3`
- PostgreSQL: `db-postgres-YYYYMMDD-HHMMSS.sql`

---

## Monitoring Backups

### Check Backup Status in Admin

1. Go to: http://127.0.0.1:8000/admin/core/activitylog/
2. Filter by: Model name = "core.Database"
3. Check latest backup status

### Check Backup Files

```powershell
# Windows
dir backups

# Linux
ls -lh backups/
```

### View Backup Logs

```bash
# Check Django logs
tail -f logs/app.log

# Filter backup logs only
findstr "backup" logs\app.log  # Windows
grep "backup" logs/app.log     # Linux
```

---

## Troubleshooting

### Issue: Task doesn't run on Windows

**Solution**:
1. Open Task Scheduler
2. Find "AgriStudies DB Backup"
3. Right-click → Properties
4. Check "Run whether user is logged on or not"
5. Make sure python path is correct
6. Test: Right-click → Run

### Issue: Permission denied

**Windows**:
- Run Task Scheduler as Administrator
- Check file permissions on `backups/` folder

**Linux**:
```bash
# Make sure cron has permissions
chmod +x manage.py
chmod 755 backups/
```

### Issue: Python not found

**Windows Task Scheduler**:
- Use full path to python.exe
- Example: `C:\Users\PC\AppData\Local\Programs\Python\Python313\python.exe`

### Issue: Backups not rotating

The system keeps backups for 7 days by default. To change:

```bash
python manage.py backup_db --keep-days=14
```

Or modify Task Scheduler action arguments:
```
manage.py backup_db --keep-days=14
```

---

## Testing the Setup

### Test Manual Backup

```bash
python manage.py backup_db
```

**Expected**:
- New file in `backups/` folder
- Success message in console
- Activity log entry in admin

### Test Scheduled Backup

```bash
python manage.py scheduled_backup
```

**Expected**:
- New backup file created
- Notification sent to all admin users
- Activity log entry with "scheduled_backup" object_id

### Test Windows Task

1. Open Task Scheduler
2. Find "AgriStudies DB Backup"
3. Right-click → Run
4. Check Last Run Result: "The operation completed successfully. (0x0)"
5. Check `backups/` folder for new file

---

## Backup Retention Policy

**Default Policy**:
- Keep backups for **7 days**
- Older backups are automatically deleted
- Runs **daily at 5:00 PM**

**Customization**:
```bash
# Keep for 30 days
python manage.py backup_db --keep-days=30

# Keep for 14 days
python manage.py backup_db --keep-days=14
```

---

## Security Best Practices

1. **Backup Directory Permissions**:
   - Windows: Restrict access to Administrators only
   - Linux: `chmod 700 backups/`

2. **Store Backups Offsite**:
   - Copy backups to cloud storage (Google Drive, Dropbox, AWS S3)
   - Use automated sync tools

3. **Encrypt Backups**:
   ```bash
   # Example: 7zip with password
   7z a -p"your-password" backup.7z backups/
   ```

4. **Test Restore Regularly**:
   ```bash
   # SQLite restore
   cp backups/db-sqlite-20250103-170000.sqlite3 db.sqlite3
   
   # PostgreSQL restore
   psql dbname < backups/db-postgres-20250103-170000.sql
   ```

---

## Next Steps

1. ✅ Choose your platform (Windows/Linux)
2. ✅ Follow setup instructions above
3. ✅ Test manual backup
4. ✅ Set up automatic scheduling
5. ✅ Test scheduled task
6. ✅ Monitor first automatic backup
7. ✅ Set up offsite backup storage (recommended)

---

## Quick Reference

### Windows Commands

```powershell
# Create task (run as Admin)
# Use Task Scheduler GUI or PowerShell script above

# Test backup
python manage.py backup_db

# Test scheduled backup
python manage.py scheduled_backup

# Check backups
dir backups

# View logs
type logs\app.log
```

### Linux Commands

```bash
# Install cron jobs
python manage.py crontab add

# Show installed jobs
python manage.py crontab show

# Remove jobs
python manage.py crontab remove

# Test backup
python manage.py backup_db

# Check cron logs
grep CRON /var/log/syslog
```

---

**Status**: ⚠️ **Requires One-Time Setup**  
**After Setup**: ✅ **Fully Automatic**  
**Maintenance**: ✅ **Zero - Runs automatically**
