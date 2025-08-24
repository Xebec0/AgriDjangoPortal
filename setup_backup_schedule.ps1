# PowerShell script to create a scheduled task for automatic backups
# Run this script as Administrator

$taskName = "AgriDjangoPortal Daily Backup"
$taskDescription = "Runs daily backup of AgriDjangoPortal database at 5:00 PM"
$scriptPath = "C:\Users\lenovo\Desktop\AgriDjangoPortal\AgriDjangoPortal\run_backup.bat"
$workingDirectory = "C:\Users\lenovo\Desktop\AgriDjangoPortal\AgriDjangoPortal"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the action (what to run)
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`"" -WorkingDirectory $workingDirectory

# Create the trigger (when to run - daily at 5:00 PM)
$trigger = New-ScheduledTaskTrigger -Daily -At 5:00PM

# Create the principal (who runs it)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

# Create the settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $taskName -Description $taskDescription -Action $action -Trigger $trigger -Principal $principal -Settings $settings
    
    Write-Host "Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $taskName"
    Write-Host "  Schedule: Daily at 5:00 PM"
    Write-Host "  Script: $scriptPath"
    Write-Host ""
    Write-Host "To test the task immediately, run:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName 'AgriDjangoPortal Daily Backup'"
    Write-Host ""
    Write-Host "To view task status, run:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName 'AgriDjangoPortal Daily Backup' | Get-ScheduledTaskInfo"
    
} catch {
    Write-Host "Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as Administrator" -ForegroundColor Yellow
}
