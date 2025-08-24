@echo off
REM Windows batch script to run Django backup
REM This script should be scheduled using Windows Task Scheduler

cd /d "C:\Users\lenovo\Desktop\AgriDjangoPortal\AgriDjangoPortal"

echo Starting backup at %date% %time% >> backup_log.txt

python manage.py scheduled_backup >> backup_log.txt 2>&1

echo Backup completed at %date% %time% >> backup_log.txt
echo ---------------------------------------- >> backup_log.txt
