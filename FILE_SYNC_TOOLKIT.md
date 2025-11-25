# 🔄 File Synchronization Toolkit

This package contains tools to keep media files synchronized across multiple development machines and deployments.

---

## 📦 What's Included

### 1. **media_sync.py** - Media Storage Diagnostic & Sync Tool
Automatically manages AWS S3 and local file synchronization.

**Commands:**
```bash
# Check current storage configuration
python media_sync.py diagnose

# Upload local media files to S3
python media_sync.py push

# Download media files from S3 locally
python media_sync.py pull
```

**Output Example:**
```
============================================================
📁 Media Storage Diagnostic
============================================================

📊 Configuration Status:
  USE_S3 setting: False
  AWS credentials configured: False
  Local media files: 91

💾 Storage Backend:
  ✅ Using Local Storage (/media folder)
     Files: 91

🔧 Recommendations:
  ✅ Local storage with files - all good!
```

---

### 2. **backup_media.py** - Media Backup Manager
Create, restore, and manage timestamped backups of media files.

**Commands:**
```bash
# Create a new backup with optional description
python backup_media.py create "Before launching to production"

# List all backups
python backup_media.py list

# List backups with detailed file listing
python backup_media.py list -v

# Restore a specific backup
python backup_media.py restore media_backup_20241215_143022

# Delete an old backup
python backup_media.py delete media_backup_20241215_143022

# Keep only 5 most recent backups
python backup_media.py cleanup 5
```

**Backup Features:**
- 📁 Automatic ZIP compression
- 📋 JSON manifest with file listing and sizes
- 🏷️ Optional descriptions for each backup
- 📊 Shows backup date, size, and file count
- 🗑️ Automatic cleanup of old backups

---

## 🚀 Quick Start

### Development Setup (Local Team)

**Step 1: Initialize Git LFS** (One-time setup)
```bash
git lfs install
git lfs track "media/**"
git add .gitattributes
git commit -m "Setup Git LFS for media files"
git push
```

**Step 2: Create first backup**
```bash
python backup_media.py create "Initial media setup"
```

**Step 3: When pulling on another device**
```bash
git pull  # Automatically gets media files via LFS

# Verify everything is in place
python media_sync.py diagnose
```

---

### Production Setup (AWS S3)

**Step 1: Configure AWS credentials in `.env`**
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=agri-app-media
AWS_S3_REGION_NAME=us-east-1
```

**Step 2: Verify S3 is configured**
```bash
python media_sync.py diagnose
```

**Step 3: Push all files to S3**
```bash
python media_sync.py push
```

**Step 4: On other machines**
```bash
# Files will auto-download from S3 on first request
# Or manually pull:
python media_sync.py pull
```

---

## 🔄 Synchronization Workflows

### Workflow 1: Git LFS (Recommended for Teams)
```
Device A (upload file) 
  ↓
git push (LFS handles large file)
  ↓
Device B
  ↓
git pull (auto-downloads via LFS)
  ↓
✅ File appears automatically
```

### Workflow 2: AWS S3 + Manual Sync
```
Device A (upload file)
  ↓
File saved to local media/
  ↓
python media_sync.py push
  ↓
Device B
  ↓
python media_sync.py pull
  ↓
✅ File downloaded from S3
```

### Workflow 3: Backup Script (Simple Sharing)
```
Device A (upload file)
  ↓
python backup_media.py create "Latest files"
  ↓
Share backup_media_TIMESTAMP.zip
  ↓
Device B
  ↓
python backup_media.py restore media_backup_TIMESTAMP
  ↓
✅ Files restored from backup
```

### Workflow 4: Hybrid (S3 + Backups)
```
Daily:
  python backup_media.py create "Daily backup"

Weekly:
  python media_sync.py push  # Also backup to S3

Before Major Changes:
  python backup_media.py create "Before refactoring"
```

---

## 📋 Configuration

### Environment Variables (.env)

**For Local Storage:**
```bash
USE_S3=False
MEDIA_ROOT=media
```

**For AWS S3:**
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_STORAGE_BUCKET_NAME=agri-app-media
AWS_S3_REGION_NAME=us-east-1
```

**Optional S3 Settings:**
```bash
AWS_S3_CUSTOM_DOMAIN=your-bucket-name.s3.amazonaws.com
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_S3_ADDRESSING_STYLE=virtual
```

---

## 🛡️ Security Best Practices

### AWS S3 Security
```
✅ DO:
- Use IAM user with S3-only permissions
- Store credentials in .env (never commit)
- Enable S3 bucket versioning
- Use CloudFront for CDN acceleration
- Enable server-side encryption (S3 default)

❌ DON'T:
- Commit AWS keys to repository
- Share access keys via email
- Use root AWS account credentials
- Make bucket publicly readable
```

### Backup Security
```
✅ DO:
- Store backups in secure location
- Encrypt sensitive backups
- Keep offsite copies (cloud backup)
- Limit access permissions (chmod 600)
- Document backup schedule

❌ DON'T:
- Store backups in public folders
- Email backups unencrypted
- Keep only one copy
- Ignore backup integrity
```

### Git LFS Security
```
✅ DO:
- Add sensitive files to .gitattributes
- Use HTTPS for Git operations
- Review .gitignore before LFS migration
- Keep LFS server credentials secure

❌ DON'T:
- Track credentials with LFS
- Push to public repositories
- Forget to initialize Git LFS
```

---

## 🐛 Troubleshooting

### Problem: "File not found on other device"
```bash
# Check if files exist locally
python media_sync.py diagnose

# If using Git LFS, check if LFS is initialized
git lfs ls-files

# If using S3, verify credentials
python media_sync.py diagnose

# Then sync
python media_sync.py pull  # For S3
git pull  # For Git LFS
```

### Problem: "AWS credentials not found"
```bash
# Check .env file exists in project root
ls -la .env

# Verify variables are set
echo $AWS_ACCESS_KEY_ID
echo $AWS_STORAGE_BUCKET_NAME

# Reload environment (restart terminal/IDE)
```

### Problem: "Backup restore failed"
```bash
# Check backup exists
python backup_media.py list

# Verify backup file integrity
unzip -t backups/media_backup_TIMESTAMP.zip

# Check disk space
df -h

# Check permissions on media folder
ls -ld media/
```

### Problem: "S3 push/pull is slow"
```bash
# This is normal for first sync
# Subsequent syncs only update changed files
# For large files, consider:
# - Using CloudFront CDN
# - Uploading to region closer to you
# - Running during off-peak hours
```

---

## 📊 File Structure

```
project/
├── media/                          # User uploaded files
│   ├── profile_images/
│   ├── documents/
│   └── ... other uploads
│
├── backups/                        # Local backup files
│   ├── media_backup_20241215_143022.zip
│   └── media_backup_20241215_143022_manifest.json
│
├── media_sync.py                   # Diagnostic & S3 sync tool
├── backup_media.py                 # Backup manager
└── MULTI_DEVICE_SYNC_QUICK_START.md  # Setup guide
```

---

## 🔗 Related Files

- **FILE_SYNC_SETUP.md** - Detailed setup for each method
- **MULTI_DEVICE_SYNC_QUICK_START.md** - Quick reference guide
- **.env.example** - Environment variable template
- **requirements.txt** - Includes boto3 for S3 support

---

## 📈 Performance & Costs

### AWS S3
- **Setup Time**: 10 minutes
- **Monthly Cost**: ~$0.50-$2 (typical usage)
- **Performance**: Fast downloads via CloudFront
- **Bandwidth**: 1GB free tier

### Git LFS
- **Setup Time**: 3 minutes
- **Monthly Cost**: Free (1GB limit)
- **Performance**: Automatic with git pull
- **Bandwidth**: Included with repository

### Local Backups
- **Setup Time**: 2 minutes
- **Monthly Cost**: Free (disk space only)
- **Performance**: Instant restore
- **Storage**: Limited by disk space

---

## 🔄 Automated Workflows

### Daily Backup Script
Create `backup_daily.sh`:
```bash
#!/bin/bash
cd /path/to/project
python backup_media.py create "Daily backup $(date +%Y-%m-%d)"
python backup_media.py cleanup 7  # Keep 7 days
```

Schedule with cron (Linux/Mac):
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup_daily.sh
```

Schedule with Task Scheduler (Windows):
```
Create task running: python backup_media.py create "Daily backup"
Time: 2:00 AM daily
```

### Weekly S3 Sync
Create `sync_weekly.sh`:
```bash
#!/bin/bash
cd /path/to/project
python media_sync.py push
```

---

## 📚 Additional Resources

- [Django File Storage Documentation](https://docs.djangoproject.com/en/5.2/ref/files/storage/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [Django-Storages Documentation](https://django-storages.readthedocs.io/)

---

## 💡 Tips & Best Practices

1. **For Development**: Use Git LFS + local backups
2. **For Production**: Use AWS S3 + CloudFront CDN
3. **For Backup**: Create backup before major changes
4. **For Cleanup**: Regularly remove old backups
5. **For Security**: Never commit `.env` with real credentials

---

## ✅ Checklist for New Team Member

- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env` and update values
- [ ] Initialize Git LFS: `git lfs install`
- [ ] Pull media files: `git pull` or `python media_sync.py pull`
- [ ] Verify setup: `python media_sync.py diagnose`
- [ ] Create first backup: `python backup_media.py create "Setup complete"`
- [ ] Test by uploading a file in the application
- [ ] Verify file appears in `/media` folder

---

**Last Updated**: December 2024  
**Status**: ✅ Production Ready  
**Tested With**: Django 5.2.7, Python 3.9+
