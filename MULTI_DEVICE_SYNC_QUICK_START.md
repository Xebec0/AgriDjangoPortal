# 🔄 Multi-Device File Sync - Quick Start Guide

Your application currently has **91 media files** stored locally in the `/media` folder. Here are the best ways to keep them synced across multiple devices.

---

## 📊 Quick Diagnostic

Run this to check your current setup:

```bash
python media_sync.py diagnose
```

Expected output when local storage is being used:
```
✅ Using Local Storage (/media folder)
   Files: 91
```

---

## 🚀 Solution 1: AWS S3 (Recommended for Production)

Best for: **Production deployments, team collaboration, scalability**

### Setup Steps (5 minutes)

**Step 1: Create AWS S3 Bucket**
1. Go to [AWS S3 Console](https://s3.amazonaws.com)
2. Click "Create bucket"
3. Name: `agri-app-media` (or any unique name)
4. Region: Select closest to you
5. Block Public Access: **Keep checked** (for security)
6. Create bucket

**Step 2: Create IAM User**
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" → "Create user"
3. Name: `agri-app-user`
4. Select "Attach policies directly"
5. Search and select: `AmazonS3FullAccess`
6. Create user

**Step 3: Generate Access Keys**
1. Click on newly created user
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Choose "Application running outside AWS"
5. Copy **Access Key ID** and **Secret Access Key**

**Step 4: Update `.env` file**
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key-from-step-3
AWS_SECRET_ACCESS_KEY=your-secret-key-from-step-3
AWS_STORAGE_BUCKET_NAME=agri-app-media
AWS_S3_REGION_NAME=us-east-1
```

**Step 5: Update `settings.py`**

The code is already in `FILE_SYNC_SETUP.md` under "Option 1: Cloud Storage". Copy the settings configuration there.

**Step 6: Sync Files**
```bash
# Push current local files to S3
python media_sync.py push

# Download files on other machine
python media_sync.py pull
```

**Cost:** ~$0.50-$2/month for typical app with 91 files

---

## 💾 Solution 2: Git LFS (Best for Version Control)

Best for: **Team workflows, automatic sync with code, free tier**

### Setup Steps (3 minutes)

**Step 1: Install Git LFS**
```bash
# Windows (with Chocolatey)
choco install git-lfs

# Or download from:
# https://git-lfs.github.com/
```

**Step 2: Initialize Git LFS in your repo**
```bash
git lfs install
git lfs track "media/**"
git add .gitattributes
git commit -m "Setup Git LFS for media files"
git push
```

**Step 3: Migrate existing media files**
```bash
git lfs migrate import --include="media/*"
```

**Step 4: On other devices**
```bash
git clone <your-repo>
# Git automatically handles large media files
```

**Benefits:**
- Automatic sync when you `git pull`
- Version history for files
- Free 1GB quota per repository

---

## 🛠️ Solution 3: Manual Backup Script (Simple & Control)

Best for: **Development teams, daily backups, maximum control**

### Setup (2 minutes)

**Step 1: Create backup script**

The code is already in `FILE_SYNC_SETUP.md`. Create file `backup_media.py`:

```bash
# Create backup
python backup_media.py backup
# Output: Created backup_20241215_143022.zip

# Restore backup
python backup_media.py restore backup_20241215_143022.zip

# List backups
python backup_media.py list
```

**Step 2: Share backups**
```bash
# Copy to shared drive, Google Drive, or email
# Restore on other machine with 'restore' command
```

**For team sync:**
- Before major changes: `python backup_media.py backup`
- Share the `.zip` file with team
- Other devices: `python backup_media.py restore filename.zip`

---

## 🐳 Solution 4: Docker Volumes (For Container Deployments)

Best for: **Docker/Kubernetes deployments, persistent storage**

Add to your `docker-compose.yml`:
```yaml
services:
  web:
    build: .
    volumes:
      - media_volume:/app/media
    
  # Alternative: Use bind mount
  # volumes:
  #   - ./media:/app/media

volumes:
  media_volume:
```

---

## 📋 Comparison Table

| Solution | Setup Time | Cost | Best For | Auto-Sync |
|----------|-----------|------|----------|-----------|
| **AWS S3** | 10 min | $0.50-2/mo | Production, scaling | ✅ Yes (manual) |
| **Git LFS** | 3 min | Free (1GB) | Team, versioning | ✅ Yes (git pull) |
| **Backup Script** | 2 min | Free | Dev teams, control | ⚠️ Manual |
| **Docker Volumes** | 5 min | Free | Containerized apps | ✅ Yes (built-in) |

---

## 🔒 Security Best Practices

### For AWS S3:
```bash
# Never commit access keys!
# .gitignore should have:
.env
.env.local
*.env

# Use IAM policies to restrict access
# - Limit to specific bucket only
# - Use expiring credentials when possible
```

### For Git LFS:
```bash
# Store large files safely
# Add to .gitignore:
*.psd
*.zip
backup_*.zip
```

### For Backup Scripts:
```bash
# Encrypt sensitive backups
# Store in secure location
# Limit access permissions
# Keep offsite copies
```

---

## 🚨 Troubleshooting

**Files disappeared after pulling code?**
```bash
# Check what storage is configured
python media_sync.py diagnose

# If using S3 but no local files:
python media_sync.py pull

# If files are only local:
# Push to S3 first, then pull on other machine
python media_sync.py push
```

**"AWS credentials not found"**
```bash
# Make sure .env file has these set:
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=xxx

# Reload environment
# (might need to restart terminal/IDE)
```

**Git LFS not tracking files?**
```bash
# Check status
git lfs ls-files

# Manually track:
git lfs track "media/**"
git add .gitattributes
git commit -m "Track media with LFS"
```

---

## 📝 Recommended Setup for Your Team

For **AgriDjangoPortal**, I recommend:

### Development (Local Team)
```
Primary: Git LFS (automatic with git pull)
Backup: Manual backup script (daily)
```

### Staging/Production
```
Primary: AWS S3 (reliable, scalable)
Backup: Automated S3 backups (every 6 hours)
```

### Implementation Order
1. **Week 1**: Set up Git LFS (quick, immediate benefit)
2. **Week 2**: Add backup script to daily workflow
3. **Week 3**: Configure AWS S3 for production

---

## 🎯 Next Steps

1. **Choose your solution** based on your use case
2. **Run the setup steps** for your chosen solution
3. **Test it** by uploading a file on one device
4. **Pull on another device** and verify file exists
5. **Document your setup** in your team's wiki

---

## 📞 Need Help?

If any solution needs clarification:
- AWS S3: Check `FILE_SYNC_SETUP.md` - Option 1
- Git LFS: Check `FILE_SYNC_SETUP.md` - Option 2
- Backup Script: Check `FILE_SYNC_SETUP.md` - Option 3
- Docker: Check `FILE_SYNC_SETUP.md` - Option 4

Run diagnostic tool anytime:
```bash
python media_sync.py diagnose
```

---

**Last Updated**: 2024
**Django Version**: 5.2.7
**Status**: ✅ Ready to implement
