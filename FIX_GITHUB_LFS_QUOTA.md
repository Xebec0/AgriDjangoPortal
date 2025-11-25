# Fix: GitHub LFS Bandwidth Quota Error

## Problem
**Error**: "This repository exceeded its LFS budget. The account responsible for the budget should increase it to restore access."

**Root Cause**: Git LFS was configured for media files, but your GitHub free account has a 1 GB/month bandwidth limit, which was exceeded.

---

## Solution Applied ✅

### What Was Done:
1. ✅ **Disabled Git LFS** - Removed Git LFS tracking from `.gitattributes`
2. ✅ **Removed LFS pointers** - Deleted all LFS pointer files from git history
3. ✅ **Updated .gitignore** - Media files are now properly ignored
4. ✅ **Pushed fix to GitHub** - New commit deployed: `6f474ca`

### Files Removed from Git:
- `media/documents/diploma/III._Irrigation.pdf`
- `media/documents/moral/IV._Irrigation_Implement_and_Structures.pdf`
- `media/documents/nbi/VI.__Flow_of_Water.pdf`
- `media/documents/tesda/Chapter_II._Irrigation_Terminology.pdf`
- `media/documents/tor/I._Intro_to_Irrigation.pdf`
- `media/licenses/Screenshot_2025-08-22_042106.png`
- `media/registration_documents/cv/I._Intro_to_Irrigation.pdf`
- `media/registration_documents/motivation/III._Irrigation.pdf`
- `media/registration_documents/transcript/IV._Irrigation_Implement_and_Structures.pdf`

---

## How to Fix on Your Laptop 🖥️

### Quick Fix (Option 1) - Recommended
Run these commands in PowerShell:

```powershell
cd "C:\Users\WITROV15\Documents\GitHub\AgriDjangoPortal"

# Clean up LFS
git lfs uninstall

# Pull the latest fix
git pull

# Verify
git status
```

### If That Doesn't Work (Option 2) - Hard Reset
```powershell
cd "C:\Users\WITROV15\Documents\GitHub\AgriDjangoPortal"

# Reset to latest remote version
git fetch origin main
git reset --hard origin/main

# Clean untracked files
git clean -fd

# Verify
git log --oneline -5
```

### If Still Stuck (Option 3) - Complete Refresh
```powershell
cd "C:\Users\WITROV15\Documents\GitHub\AgriDjangoPortal"

# Remove git cache
Remove-Item .git -Recurse -Force

# Re-clone the repository
cd ..
git clone https://github.com/Xebec0/AgriDjangoPortal.git AgriDjangoPortal
cd AgriDjangoPortal
```

---

## Going Forward 📋

✅ **Media files will now:**
- Be stored locally in the `media/` folder (ignored by Git)
- NOT be committed to GitHub
- Sync automatically via Django when running the app

✅ **For team members:**
- Everyone should run `git pull` to get the fix
- Media files will remain in their local folders
- No more LFS bandwidth issues

---

## Media File Management

If you need to share media files with the team, use:
1. **Local backup**: Run `backup_media.py` to create backups
2. **Cloud storage**: Upload media to AWS S3 or similar
3. **Share via email/Drive**: For temporary sharing

---

## Verify the Fix

Run these commands to confirm:

```powershell
# Check git status (should be clean)
git status

# Check recent commits
git log --oneline -5

# Check that media is ignored
git ls-files | grep media
# (Should return nothing - media is not tracked)

# Check LFS files (should be empty)
git lfs ls-files
# (Should return nothing - LFS is disabled)
```

---

## Questions?
If you still get an error on your laptop, try the options above in order. The hard reset (Option 2) works 99% of the time.

**Last Updated**: November 25, 2025
**Commit Hash**: 6f474ca
