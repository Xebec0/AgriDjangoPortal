# Multi-Device Sync - Quick Reference Card

## TL;DR - 30 Second Setup

**Device A (You have files):**
```powershell
.\backup_media.ps1
# Share media_backup_*.zip file
```

**Device B (You need files):**
```powershell
# Download media_backup_*.zip to AgriDjangoPortal folder
.\restore_media.ps1
# Done! Run Django normally
```

---

## Common Commands

### Create Backup
```powershell
.\backup_media.ps1
```
Creates: `media_backup_YYYYMMDD_HHMMSS.zip`

### Restore Backup
```powershell
.\restore_media.ps1
```
Extracts all files to `media/` folder

### Check Backup Size
```powershell
Get-Item media_backup_*.zip | Select-Object Name, Length
```

### List Backup Contents
```powershell
[System.Reflection.Assembly]::LoadWithPartialName("System.IO.Compression.FileSystem") | Out-Null
[System.IO.Compression.ZipFile]::OpenRead((Get-Item media_backup_*.zip).FullName).Entries | Select-Object FullName
```

### Count Media Files
```powershell
(Get-ChildItem media -Recurse -File).Count
```

### Check Media Folder Size
```powershell
'{0:N2} MB' -f ((Get-ChildItem media -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB)
```

---

## Sharing Methods

| Method | Time | Ease | Best For |
|--------|------|------|----------|
| Google Drive | Fast | Easy | Remote teams |
| Dropbox | Fast | Easy | Remote teams |
| OneDrive | Fast | Easy | Remote teams |
| Email | Medium | Easy | Small teams |
| USB Drive | Very Fast | Easy | Local teams |
| WeTransfer | Fast | Easy | One-time sharing |

---

## Workflow Examples

### Example 1: Daily Updates
```powershell
# Device A (Your PC):
# 1. Upload files through Django admin
# 2. Create new backup:
.\backup_media.ps1

# 3. Upload new zip to Google Drive
# 4. Notify team: "New backup ready"

# Device B (Team member):
# 1. Download latest zip from Google Drive
# 2. Place in AgriDjangoPortal folder
# 3. Run restore:
.\restore_media.ps1
# 4. Use Django normally
```

### Example 2: Multiple Uploads Per Day
```powershell
# Device A:
# Upload 1: .\backup_media.ps1 -> Share backup_morning.zip
# Upload 2: .\backup_media.ps1 -> Share backup_afternoon.zip
# Upload 3: .\backup_media.ps1 -> Share backup_evening.zip

# Device B:
# Download latest backup
# .\restore_media.ps1
```

---

## File Locations

```
Your Project/
└── media_backup_*.zip          <-- Download this
└── media/                       <-- Extracted here after restore
└── backup_media.ps1            <-- Creates backup
└── restore_media.ps1           <-- Restores backup
└── SETUP_COMPLETE.md           <-- Full documentation
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "file not found" errors | Run `.\restore_media.ps1` |
| Backup won't create | Check `media/` folder exists |
| Restore won't work | Verify backup file in root folder |
| Files still missing | Download latest backup from team |

---

## Facts

- **Total files:** 91 media files
- **Backup size:** ~7 MB (compressed)
- **Extract time:** < 1 minute
- **Cost:** FREE (no GitHub limits!)
- **Reliability:** 100% (just zip files)

---

## For Your Team

**Send them this file and they'll know everything they need!**

```
Steps:
1. Get media_backup_*.zip from shared location
2. Place it in AgriDjangoPortal folder
3. Open PowerShell
4. Run: .\restore_media.ps1
5. Done! Use Django normally
```

---

Last Updated: 2025-11-25
