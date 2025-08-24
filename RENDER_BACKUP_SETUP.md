# Automatic Backup Configuration for Render.com

## ✅ YES - Automatic Backups Will Work on Render!

The automatic backup system has been configured to work on both:
1. **Local Windows Development** - Using Windows Task Scheduler
2. **Render.com Production** - Using Render's native Cron Jobs

## Render.com Configuration

### What Was Added to `render.yaml`:

```yaml
# Cron job for automatic daily backups at 5:00 PM UTC
- type: cron
  name: agridjangoportal-backup
  env: python
  schedule: "0 17 * * *"  # Daily at 5:00 PM UTC
  buildCommand: pip install -r requirements.txt
  startCommand: python manage.py scheduled_backup
  envVars:
    - key: DATABASE_URL
      fromDatabase:
        name: "agri-db"
        property: connectionString
    - key: SECRET_KEY
      generateValue: true
    - key: DEBUG
      value: false
```

### How It Works on Render:

1. **Cron Service Type**: Render has a dedicated `cron` service type for scheduled tasks
2. **Schedule**: `"0 17 * * *"` = Daily at 5:00 PM UTC
3. **Command**: Runs `python manage.py scheduled_backup`
4. **Database Access**: Uses the same PostgreSQL database as the main app
5. **Automatic**: No manual setup needed - deploys with your app

## Deployment Instructions for Render

### Step 1: Deploy Your Application
```bash
git add .
git commit -m "Add automatic backup system with Render cron job"
git push origin main
```

### Step 2: Connect to Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Create new Blueprint Instance or Web Service
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`

### Step 3: Verify Cron Job Creation
After deployment, you'll see TWO services in your Render dashboard:
1. **agridjangoportal** - Your main web application
2. **agridjangoportal-backup** - The cron job for backups

### Step 4: Monitor Backups
- Check Render dashboard → agridjangoportal-backup → Logs
- Backups will run daily at 5:00 PM UTC
- Look for "Scheduled backup completed successfully" in logs

## Important Notes for Production

### 1. Backup Storage on Render
**⚠️ IMPORTANT**: Render's free tier has ephemeral storage. Backup files stored locally will be lost on redeploy.

**Solutions**:
1. **Use External Storage** (Recommended):
   - Amazon S3
   - Google Cloud Storage
   - Dropbox API
   - Any cloud storage service

2. **Database-to-Database Backup**:
   - Create a separate backup database
   - Copy data between databases

3. **Export via Email**:
   - Email backup files to admin
   - Store in email archive

### 2. Time Zone Considerations
- Render uses **UTC time** by default
- `"0 17 * * *"` = 5:00 PM UTC
- Adjust for your local timezone:
  - EST: 12:00 PM (noon)
  - PST: 9:00 AM
  - CET: 6:00 PM
  - IST: 10:30 PM

### 3. Notification System
On Render, notifications will:
- Be created in the database for admin users
- Show in the web interface notification dropdown
- NOT send emails unless you configure SMTP settings

## Comparison: Local vs Render

| Feature | Local (Windows) | Render.com |
|---------|----------------|------------|
| Scheduler | Windows Task Scheduler | Render Cron Jobs |
| Schedule Format | PowerShell Task | Cron expression |
| Backup Storage | Local `backups/` folder | Ephemeral (needs external storage) |
| Database | SQLite | PostgreSQL |
| Notifications | Local + Console | Database + Web UI |
| Setup Method | Run PowerShell script | Automatic via render.yaml |
| Manual Trigger | Task Scheduler UI | Render Dashboard |

## Testing on Render

After deployment, test the backup system:

1. **Manual Test** (via Render Shell):
   ```bash
   python manage.py scheduled_backup
   ```

2. **Check Logs**:
   - Navigate to agridjangoportal-backup service
   - View Logs tab
   - Look for execution at scheduled time

3. **Verify Notifications**:
   - Log in as admin on your deployed site
   - Check notification dropdown
   - Should see backup success/failure messages

## Modifying Backup Schedule on Render

To change the backup time:

1. Edit `render.yaml`
2. Change the `schedule` field:
   ```yaml
   schedule: "0 9 * * *"   # 9:00 AM UTC
   schedule: "0 */6 * * *" # Every 6 hours
   schedule: "0 2 * * 0"   # Weekly on Sunday at 2 AM
   ```
3. Commit and push changes
4. Render will automatically update the cron job

## Monitoring and Alerts

### Set up Render Alerts:
1. Go to your service settings
2. Configure failure notifications
3. Add email/Slack webhooks
4. Get notified if backups fail

### Check Backup Status:
- Admin Panel → Activity Logs
- Filter by model_name='core.Database'
- View backup history and status

## Troubleshooting

### If Backups Don't Run on Render:
1. Check service logs for errors
2. Verify DATABASE_URL is set correctly
3. Ensure cron service is "Live" status
4. Check for Python/Django errors in logs

### Common Issues:
- **"No module named 'core'"**: Ensure DJANGO_SETTINGS_MODULE is set
- **"Database connection failed"**: Check DATABASE_URL environment variable
- **"Permission denied"**: Verify database user has backup permissions

## Summary

✅ **Your automatic backup system is now configured for BOTH environments:**
- **Local Development**: Windows Task Scheduler runs at 5:00 PM daily
- **Render Production**: Cron job service runs at 5:00 PM UTC daily

The system will automatically create backups, send notifications, and maintain audit logs in both environments. Just deploy to Render and the cron job will be created automatically!
