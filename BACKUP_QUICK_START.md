# 🔄 Automatic Backup - Quick Start

## Problem Fixed ✅

**Issue**: Automatic backups were configured but not actively running  
**Cause**: Windows Task Scheduler requires manual one-time setup  
**Solution**: Simple activation process below  

---

## Quick Setup (3 Steps)

### Step 1: Test Backup Works

```bash
python manage.py setup_auto_backup --test
```

**Expected**: See "✓ Backup test successful!" with a new backup file created

---

### Step 2: Get Setup Command

```bash
python manage.py setup_auto_backup --show-command
```

This will show a PowerShell script to create the scheduled task.

---

### Step 3: Create Scheduled Task

**Option A: Copy PowerShell Script (Easiest)**

1. Run the command from Step 2
2. Copy the PowerShell script output
3. Open **PowerShell as Administrator**
4. Paste and run the script
5. Done! Backup will run daily at 5:00 PM

**Option B: Manual Setup via GUI**

1. Press `Win + R`, type `taskschd.msc`, Enter
2. Click "Create Task"
3. Name: `AgriStudies DB Backup`
4. Check: "Run whether user is logged on or not"
5. **Triggers Tab**: New → Daily at 17:00 (5 PM)
6. **Actions Tab**: New →
   - Program: `C:\Users\PC\AppData\Local\Programs\Python\Python313\python.exe`
   - Arguments: `manage.py scheduled_backup`
   - Start in: `C:\Users\PC\Documents\GitHub\AgriDjangoPortal`
7. Click OK → Enter password if prompted
8. Right-click task → Run (to test)

---

## Verify It's Working

### Check Task Status (Windows)

```powershell
Get-ScheduledTask -TaskName "AgriStudies DB Backup"
```

### View Backups

```bash
dir backups
```

### Check in Admin Panel

Go to: http://127.0.0.1:8000/admin/core/activitylog/

Filter by: **Model name = "core.Database"**

---

## Backup Schedule

- **When**: Daily at 5:00 PM (17:00)
- **Where**: `C:\Users\PC\Documents\GitHub\AgriDjangoPortal\backups\`
- **Retention**: 7 days (automatically deletes older backups)
- **Notifications**: Admins get notified of success/failure

---

## Customization

### Change Backup Time

```bash
python manage.py setup_auto_backup --time 20:00
```

Then follow Step 3 again to create task with new time.

### Change Retention Period

Edit the scheduled task action arguments:
```
manage.py backup_db --keep-days=30
```

---

## Manual Backup Anytime

```bash
# Quick backup
python manage.py backup_db

# With notifications to admins
python manage.py scheduled_backup
```

---

## Troubleshooting

### Issue: Task doesn't run

1. Open Task Scheduler
2. Find "AgriStudies DB Backup"
3. Check "Last Run Result" - should be "0x0" (success)
4. If failed, check:
   - Python path is correct
   - Working directory is correct
   - "Run whether user is logged on or not" is checked

### Issue: No backups in folder

1. Run test: `python manage.py setup_auto_backup --test`
2. Check permissions on `backups/` folder
3. Check Task Scheduler history

### Issue: Permission denied

- Run PowerShell **as Administrator**
- Check folder permissions
- Ensure user account has rights to run scheduled tasks

---

## Full Documentation

See: **`docs/AUTOMATIC_BACKUP_SETUP.md`** for complete guide

---

**Status**: ✅ Ready to Activate  
**Time Required**: 2 minutes  
**Difficulty**: Easy  
**Support**: See docs folder for detailed guide
