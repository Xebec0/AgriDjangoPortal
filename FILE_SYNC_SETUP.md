# 📁 Multi-Device File Sync Setup Guide

This guide explains how to sync uploaded media files across multiple development machines and production environments.

## 🎯 Overview

When you develop on multiple devices, you need media files (uploads, images, documents) to be accessible on all machines. This guide provides solutions from simple to advanced.

---

## Option 1: Cloud Storage (AWS S3) - **Recommended for Production**

### ✅ Pros:
- Automatic sync across all devices
- Highly scalable and reliable
- Professional solution for production
- Easy team collaboration
- No Git repository bloat

### ❌ Cons:
- Costs money ($0.023/GB per month minimum for development)
- Requires AWS account setup
- Internet dependency

### Setup Instructions:

#### Step 1: Install Dependencies
```bash
pip install boto3 django-storages
pip install -r requirements.txt  # Includes the above
```

#### Step 2: Create AWS S3 Bucket
1. Go to [AWS Console](https://console.aws.amazon.com)
2. Create S3 bucket: `agristudies-media-dev` (for development)
3. In bucket settings:
   - Allow public read access (for development)
   - Enable versioning (optional, for backups)

#### Step 3: Create IAM User for S3 Access
1. Go to IAM → Users → Create User
2. Name: `agristudies-app`
3. Attach policy: `AmazonS3FullAccess`
4. Generate access key and secret key
5. **Save these securely** - you'll need them next

#### Step 4: Add Environment Variables

Create or update `.env` file:
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_STORAGE_BUCKET_NAME=agristudies-media-dev
AWS_S3_REGION_NAME=us-east-1

# Set to True for production, False for development (uses local storage)
USE_S3=False
```

#### Step 5: Update settings.py

Add this to your `agrostudies_project/settings.py`:

```python
import os
from pathlib import Path

# ... existing code ...

# File Storage Configuration
USE_S3 = os.getenv('USE_S3', 'False').lower() == 'true'

if USE_S3:
    # AWS S3 Storage Settings
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
                'region_name': os.getenv('AWS_S3_REGION_NAME', 'us-east-1'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'default_acl': 'public-read',
            }
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
                'region_name': os.getenv('AWS_S3_REGION_NAME', 'us-east-1'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'default_acl': 'public-read',
            }
        }
    }
    # AWS S3 URL configuration
    AWS_S3_CUSTOM_DOMAIN = f'{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # Local File Storage (Development)
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATIC_URL = '/static/'
```

#### Step 6: Test it Out

1. Upload a file through your Django app
2. File should appear in your S3 bucket automatically
3. On another device, pull the code and `.env`
4. Set `USE_S3=True` in that `.env` file
5. Files should be accessible immediately!

---

## Option 2: Git LFS (Large File Storage) - **Good for Small Projects**

### ✅ Pros:
- Files are versioned like code
- Automatically synced with Git
- Works across all devices automatically
- Free (1GB on GitHub)

### ❌ Cons:
- Slower than regular Git
- Limited free storage (1GB)
- Must install Git LFS extension
- Paid plan for large projects

### Setup Instructions:

#### Step 1: Install Git LFS
```bash
# Windows
choco install git-lfs

# macOS
brew install git-lfs

# Linux
apt-get install git-lfs
```

#### Step 2: Initialize Git LFS
```bash
cd c:\Users\PC\Documents\GitHub\AgriDjangoPortal
git lfs install
```

#### Step 3: Track Media Files
```bash
# Track common upload extensions
git lfs track "*.jpg" "*.jpeg" "*.png" "*.pdf" "*.docx" "*.xlsx"

# Or track entire media folder
git lfs track "media/**"

# Add the .gitattributes file
git add .gitattributes
git commit -m "Configure Git LFS for media files"
```

#### Step 4: Add Media Folder to Git
```bash
git add media/
git commit -m "Add media files to Git LFS"
git push origin main
```

#### Step 5: On Another Device
```bash
git clone https://github.com/Xebec0/AgriDjangoPortal.git
cd AgriDjangoPortal

# Git LFS automatically downloads files
git lfs pull
```

---

## Option 3: Manual Sync with Backup Script - **Best for Dev Teams**

### ✅ Pros:
- No external services needed
- Easy to understand and control
- Great for backups
- Works offline

### ❌ Cons:
- Manual process
- Not real-time
- Requires setup on each device

### Setup Instructions:

Create `backup_media.py` in project root:

```python
import os
import shutil
import json
from datetime import datetime
from pathlib import Path

MEDIA_DIR = Path('media')
BACKUP_DIR = Path('media_backups')
MANIFEST_FILE = BACKUP_DIR / 'manifest.json'

def create_manifest():
    """Create a manifest of all media files"""
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'files': {}
    }
    
    if MEDIA_DIR.exists():
        for file_path in MEDIA_DIR.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(MEDIA_DIR)
                manifest['files'][str(relative_path)] = {
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
    
    return manifest

def backup_media():
    """Backup all media files"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    manifest = create_manifest()
    
    if MEDIA_DIR.exists():
        backup_path = BACKUP_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(MEDIA_DIR, backup_path)
        print(f"✅ Backup created: {backup_path}")
    
    # Save manifest
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"✅ Manifest saved: {MANIFEST_FILE}")

def restore_media(backup_name):
    """Restore media from a backup"""
    backup_path = BACKUP_DIR / backup_name
    
    if not backup_path.exists():
        print(f"❌ Backup not found: {backup_path}")
        return False
    
    # Remove old media
    if MEDIA_DIR.exists():
        shutil.rmtree(MEDIA_DIR)
    
    # Restore from backup
    shutil.copytree(backup_path, MEDIA_DIR)
    print(f"✅ Media restored from: {backup_path}")
    return True

def list_backups():
    """List all available backups"""
    if not BACKUP_DIR.exists():
        print("No backups found")
        return
    
    backups = sorted([d.name for d in BACKUP_DIR.iterdir() if d.is_dir()])
    print("Available backups:")
    for backup in backups:
        print(f"  - {backup}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python backup_media.py [backup|restore|list]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'backup':
        backup_media()
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Usage: python backup_media.py restore <backup_name>")
            list_backups()
        else:
            restore_media(sys.argv[2])
    elif command == 'list':
        list_backups()
    else:
        print(f"Unknown command: {command}")
```

Usage:

```bash
# Create a backup
python backup_media.py backup

# List backups
python backup_media.py list

# Restore from backup
python backup_media.py restore backup_20251125_143022

# Then commit and push
git add media_backups/manifest.json
git commit -m "Update media manifest"
git push origin main
```

---

## Option 4: Docker Volumes - **Best for Container Deployments**

If using Docker, add to `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    volumes:
      - media_volume:/app/media
      - static_volume:/app/staticfiles

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  media_volume:
  static_volume:
  postgres_data:
```

---

## 🎯 Recommended Setup for Your Project

For **AgriDjangoPortal**, I recommend:

### Development (Local):
- Use **Option 1 (AWS S3)** with `USE_S3=False` (local storage)
- Create backups with Option 3 before major changes

### Production (Render/Heroku):
- Use **Option 1 (AWS S3)** with `USE_S3=True`
- Costs < $1/month for typical usage
- Automatic sync across instances

### Team Collaboration:
- Use **Option 2 (Git LFS)** for small projects
- Or **Option 1 (AWS S3)** for professional deployments

---

## ⚠️ Important Security Notes

1. **Never commit `.env` file** - Always add to `.gitignore`:
   ```bash
   echo ".env" >> .gitignore
   git rm --cached .env
   ```

2. **Protect AWS Credentials**:
   - Use IAM roles instead of access keys when possible
   - Rotate keys every 90 days
   - Enable MFA on AWS account

3. **S3 Bucket Permissions**:
   - Development: Can be public
   - Production: Must be private + CloudFront CDN

---

## 📊 Comparison Table

| Feature | S3 | Git LFS | Backup Script | Docker |
|---------|----|---------|----|--------|
| **Automatic sync** | ✅ | ✅ | ❌ | ✅ |
| **Cost** | Low | Free | Free | Free |
| **Setup difficulty** | Medium | Easy | Easy | Medium |
| **Team friendly** | ✅ | ✅ | ❌ | ✅ |
| **Production ready** | ✅ | ✅ | ❌ | ✅ |
| **Real-time** | ✅ | ✅ | ❌ | ✅ |
| **Scalability** | ✅ | Limited | Limited | ✅ |

---

## Quick Start

### For Production (AWS S3):
```bash
# 1. Install
pip install boto3 django-storages

# 2. Create S3 bucket and IAM user

# 3. Update .env with credentials

# 4. Update settings.py (code provided above)

# 5. Test by uploading a file
```

### For Development (Local + Backups):
```bash
# Just use default settings, files go to /media folder
# Periodically run backups:
python backup_media.py backup
```

---

Have questions? Ask your AI assistant for clarification on any option!
