# Git LFS Setup Guide - AgriDjangoPortal

## What is Git LFS?

Git LFS (Large File Storage) is a Git extension that stores large files (like images, videos, documents) outside of your Git repository. Instead of storing the actual files, Git stores pointers to them.

**Key Benefits:**
- 🚀 Faster cloning and pulling
- 💾 Smaller repository size
- 🔄 Automatic file sync across devices
- 📝 Works seamlessly with existing Git workflow

---

## How It Works

```
Device A (uploads file)
    ↓
git add . && git commit && git push
    ↓
Git LFS intercepts large files
    ↓
Files stored in Git LFS server
Pointers stored in Git repository
    ↓
Device B
    ↓
git clone or git pull
    ↓
Git LFS automatically downloads files ✅
```

---

## Setup Instructions (3 Steps)

### Step 1: Install Git LFS

**Option A: Using Setup Script (Recommended)**
```powershell
cd c:\Users\PC\Documents\GitHub\AgriDjangoPortal
.\setup_git_lfs.ps1
```

**Option B: Manual Installation**

1. Go to: https://git-lfs.github.com/
2. Download the Windows installer
3. Run the installer
4. Close and reopen PowerShell

**Verify Installation:**
```powershell
git lfs --version
# Should output: git-lfs/3.4.0 (GitHub; windows amd64; go 1.21.0)
```

---

### Step 2: Configure Git LFS for Your Project

Run the configuration script:
```powershell
cd c:\Users\PC\Documents\GitHub\AgriDjangoPortal
.\configure_git_lfs.ps1
```

**What This Does:**
```bash
git lfs install              # Initialize Git LFS
git lfs track "media/**"     # Track all media files
git add .gitattributes       # Stage configuration
git commit -m "Setup Git LFS" # Commit changes
```

---

### Step 3: Push to GitHub

```powershell
git push origin main
```

**Done!** 🎉 From now on, all media files will automatically sync via Git LFS.

---

## How to Use Git LFS

### Uploading Files
```bash
# Normal Git workflow - everything is automatic!
git add .
git commit -m "Added new images"
git push
# Git LFS automatically handles large files ✅
```

### Pulling Files
```bash
# Files automatically download via LFS
git pull

# Or manually pull LFS files
git lfs pull
```

### Cloning on Another Device
```bash
git clone https://github.com/Xebec0/AgriDjangoPortal.git
# Git LFS automatically downloads all media files ✅
```

---

## Useful Commands

```bash
# See all files tracked by Git LFS
git lfs ls-files

# Check which version of Git LFS is installed
git lfs --version

# Manually download all LFS files
git lfs pull

# Check Git LFS status
git lfs status

# Track a new file type (example: all PDFs)
git lfs track "*.pdf"

# View LFS configuration
git config -l | grep lfs
```

---

## What Gets Tracked?

After setup, Git LFS will track these file types in the media folder:

```
media/
├── profile_images/       ✅ (all image types)
├── documents/            ✅ (PDFs, DOCs, etc.)
├── licenses/             ✅ (image files)
├── program_images/       ✅ (image files)
├── registration_documents/ ✅ (all documents)
└── ... any other files added to media/
```

---

## Troubleshooting

### Problem: "git lfs: command not found"
**Solution:**
1. Ensure Git LFS is installed: `git lfs --version`
2. Close and reopen PowerShell to refresh environment
3. Try running installer again

### Problem: Files aren't syncing
**Solution:**
```bash
# Check if files are being tracked
git lfs ls-files

# Manually pull LFS files
git lfs pull

# Check status
git lfs status
```

### Problem: ".gitattributes" not in repository
**Solution:**
```bash
git add .gitattributes
git commit -m "Add .gitattributes"
git push
```

### Problem: Large files still in Git history
**Solution:**
Run once to clean up:
```bash
git lfs migrate import --include="media/*"
git push
```

---

## Verification Checklist

After setup, verify everything is working:

```
☑️ Git LFS is installed
   Command: git lfs --version

☑️ .gitattributes file exists and is committed
   Command: git show HEAD:.gitattributes

☑️ Files are being tracked by LFS
   Command: git lfs ls-files

☑️ Push completes successfully
   Command: git push origin main

☑️ Can clone on another device
   Clone the repo and verify media files exist
```

---

## Testing Git LFS

### Test 1: Verify Tracking
```powershell
cd c:\Users\PC\Documents\GitHub\AgriDjangoPortal
git lfs ls-files
```
**Expected:** Shows files being tracked (or "No files" if none staged)

### Test 2: Upload New File
```bash
# Add a test image
Copy-Item "media/licenses/kyla.jpg" "media/test_lfs.jpg"

# Commit it
git add media/test_lfs.jpg
git commit -m "Test Git LFS upload"
git push

# Verify it was tracked
git lfs ls-files | findstr test_lfs.jpg
```

### Test 3: Clone on Another Device
```bash
# On different machine/folder
git clone https://github.com/Xebec0/AgriDjangoPortal.git
cd AgriDjangoPortal

# Check if media files exist
ls media/
# Should show all files ✅
```

---

## Understanding .gitattributes

Your `.gitattributes` file will look like:

```
media/** filter=lfs diff=lfs merge=lfs -text
```

This tells Git:
- **media/\*\*** - Apply to all files in media folder
- **filter=lfs** - Use LFS to filter/compress
- **diff=lfs** - Use LFS for diffs
- **merge=lfs** - Use LFS for merges
- **-text** - Treat as binary (not text)

---

## Team Workflow

### New Team Member Setup
```bash
1. Clone repository
   git clone https://github.com/Xebec0/AgriDjangoPortal.git

2. Git LFS automatically pulls files
   (happens automatically)

3. Verify setup
   git lfs ls-files

4. Ready to work!
```

### Daily Workflow
```bash
# Pull latest changes (including media files)
git pull

# Make changes
# ... edit files ...

# Commit (Git LFS handles large files automatically)
git add .
git commit -m "Updated features"

# Push
git push
```

---

## Size Impact

**Before Git LFS:**
- Repository size: Very large
- Clone time: Slow
- Push/pull time: Slow

**After Git LFS:**
- Repository size: Small (only pointers)
- Clone time: Fast ⚡
- Push/pull time: Fast ⚡
- Media files: Still available via LFS

---

## Best Practices

✅ **DO:**
- Initialize Git LFS early in project
- Track media files with Git LFS
- Use .gitattributes in version control
- Train team on Git LFS workflow
- Verify files sync properly
- Keep LFS server running

❌ **DON'T:**
- Commit large files to Git without LFS
- Forget to push .gitattributes
- Share LFS server credentials
- Mix LFS and regular Git for same files
- Store credentials in tracked files

---

## Additional Resources

- **Official Docs**: https://git-lfs.github.com/
- **GitHub LFS Docs**: https://docs.github.com/en/repositories/working-with-files/managing-large-files
- **Troubleshooting**: https://github.com/git-lfs/git-lfs/wiki/Troubleshooting

---

## Summary

| Step | Action | Time | Command |
|------|--------|------|---------|
| 1 | Install Git LFS | 5 min | `.\setup_git_lfs.ps1` |
| 2 | Configure | 2 min | `.\configure_git_lfs.ps1` |
| 3 | Push | 1 min | `git push` |
| ✅ | Done! | - | - |

---

## What's Next?

After setup:
1. ✅ All media files automatically sync with Git
2. ✅ Team members auto-download files when they clone
3. ✅ No more missing file issues
4. ✅ Automatic file versioning

**Ready to set up?**

```powershell
# Step 1: Close and reopen PowerShell
# Step 2: Navigate to project
cd c:\Users\PC\Documents\GitHub\AgriDjangoPortal

# Step 3: Run setup script
.\setup_git_lfs.ps1

# Step 4: Run configuration script
.\configure_git_lfs.ps1

# Step 5: Push to GitHub
git push origin main

# Done! 🎉
```

---

**Status**: Ready to Implement  
**Time Required**: 10 minutes  
**Result**: Automatic file sync across all devices ✅
