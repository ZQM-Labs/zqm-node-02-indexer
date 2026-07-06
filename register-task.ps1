$TaskName = "ZQM-Node-02-Indexer"
$PythonExe = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python interpreter not found in PATH." -ForegroundColor Red
    exit 1
}
$AppScript = "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer\app.py"
$WorkDir = "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Start-Sleep -Seconds 1
}

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$AppScript`"" `
    -WorkingDirectory $WorkDir

# Create triggers: at startup and at logon
$Triggers = @()
$Triggers += New-ScheduledTaskTrigger -AtStartup
$Triggers += New-ScheduledTaskTrigger -AtLogOn -User "zqmco"

# Settings: auto-restart, run forever
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit 0 `
    -Priority 5

# Register the task (runs as current user with highest privileges)
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -User "zqmco" `
    -RunLevel Highest `
    -Force

if ($?) {
    Write-Host "Task '$TaskName' created successfully."
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task started."
} else {
    Write-Host "Failed to create task."
    exit 1
}