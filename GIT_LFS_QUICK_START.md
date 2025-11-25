# 📟 Git LFS - Quick Reference Card

## What You Have

```
✅ setup_git_lfs.ps1         → Installer script
✅ configure_git_lfs.ps1     → Configuration script  
✅ GIT_LFS_SETUP_GUIDE.md    → Complete documentation
✅ GIT_LFS_COMPLETE_SETUP.md → Package overview
✅ 91 media files            → Ready to sync
```

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install (5 min)
```powershell
.\setup_git_lfs.ps1
# Then close & reopen PowerShell!
```

### Step 2: Configure (2 min)
```powershell
.\configure_git_lfs.ps1
```

### Step 3: Push (1 min)
```powershell
git push origin main
```

**Total: 8 minutes** ⏱️

---

## ✅ Verify It Works

```bash
git lfs --version
# Output: git-lfs/3.4.0 (...)

git lfs ls-files
# Output: Shows tracked files

git show HEAD:.gitattributes
# Output: media/** filter=lfs ...
```

---

## 📊 After Setup

### What Happens
- ✅ All 91 media files tracked by Git LFS
- ✅ git push/pull automatically handles files
- ✅ Team members get files on clone
- ✅ Small repository size

### Normal Workflow (Unchanged!)
```bash
git add .
git commit -m "message"
git push
# Git LFS handles everything ✅
```

---

## 🔄 For Team Members

### Clone New Repo
```bash
git clone https://github.com/Xebec0/AgriDjangoPortal.git
# Files auto-downloaded via LFS ✅
```

### Update Existing Repo
```bash
git pull
# LFS automatically syncs ✅
```

---

## 📋 Useful Commands

```bash
# List LFS tracked files
git lfs ls-files

# Manually pull LFS files
git lfs pull

# Check LFS status
git lfs status

# View config
git config -l | grep lfs
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "git lfs: command not found" | Close & reopen PowerShell after install |
| "Cannot run scripts" | Run as admin or check execution policy |
| "Permission denied" | Run PowerShell as Administrator |
| "Files not syncing" | Run: git lfs pull |

---

## 📞 Need Help?

**Read These Files:**
1. GIT_LFS_COMPLETE_SETUP.md (overview)
2. GIT_LFS_SETUP_GUIDE.md (detailed guide)
3. VISUAL_SYNC_GUIDE.md (diagrams)

---

## ✨ That's It!

**Before:** Files missing on other devices → 404 errors ❌  
**After:** Files auto-sync everywhere ✅

**Time to implement:** 8 minutes  
**Result:** Automatic file sync forever

**Ready?** Run `.\setup_git_lfs.ps1` now! 🚀
