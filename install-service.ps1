<#
.SYNOPSIS
    Installs the ZQM Node-02 Workstation File Indexer as a background service
    that auto-starts on Windows boot/login.

.DESCRIPTION
    Creates a scheduled task that runs the Flask API server silently in the background.
    The task runs whether the user is logged in or not, and auto-starts on boot.
#>

$TaskName = "ZQM-Node-02-Indexer"
$ProjectDir = "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"
$PythonExe = "C:\Users\zqmco\AppData\Local\Programs\Python\Python312\pythonw.exe"
$AppScript = Join-Path $ProjectDir "app.py"
$LogFile = Join-Path $ProjectDir "service.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ZQM Node-02 Indexer Service Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if files exist
if (-not (Test-Path $AppScript)) {
    Write-Host "ERROR: app.py not found at $AppScript" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python not found at $PythonExe" -ForegroundColor Red
    exit 1
}

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing scheduled task '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Start-Sleep -Seconds 1
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$AppScript`"" `
    -WorkingDirectory $ProjectDir

# Run at system startup (before login) and also at user logon
$Triggers = @()
$Triggers += New-ScheduledTaskTrigger -AtStartup
$Triggers += New-ScheduledTaskTrigger -AtLogOn -User "zqmco"

# Run whether user is logged in or not, with highest privileges
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365) `
    -Priority 5

# Run as the current user with highest privileges
$Principal = New-ScheduledTaskPrincipal `
    -UserId "zqmco" `
    -LogonType S4U `
    -RunLevel Highest

Write-Host "Creating scheduled task '$TaskName'..." -ForegroundColor Green
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Principal $Principal `
    -Description "ZQM Node-02 Workstation File Indexer - Flask API server for file search across the entire workstation. Auto-starts on boot."

if ($?) {
    Write-Host ""
    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name:        $TaskName"
    Write-Host "  Script:      $AppScript"
    Write-Host "  Python:      $PythonExe"
    Write-Host "  Triggers:    At system startup + At user logon"
    Write-Host "  Run as:      zqmco (highest privileges)"
    Write-Host "  Auto-restart: Yes (3 attempts, 1 min interval)"
    Write-Host ""

    # Start the task now
    Write-Host "Starting the service now..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName

    Start-Sleep -Seconds 3

    # Verify it's running
    $state = (Get-ScheduledTask -TaskName $TaskName).State
    Write-Host "Service state: $state" -ForegroundColor Cyan

    # Check if the API is responding
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/stats" -TimeoutSec 5
        Write-Host ""
        Write-Host "✓ API is responding!" -ForegroundColor Green
        Write-Host "  Files indexed: $($response.document_count)"
        Write-Host "  Web UI:        http://127.0.0.1:5000"
    } catch {
        Write-Host ""
        Write-Host "⚠ Service started but API not yet responding (may take a few seconds)..." -ForegroundColor Yellow
        Write-Host "  Check http://127.0.0.1:5000 in your browser shortly."
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The indexer will now auto-start on every boot."
    Write-Host "To manage the service, use Task Scheduler or run:"
    Write-Host "  Start:    Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Stop:     Stop-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Status:   (Get-ScheduledTask -TaskName '$TaskName').State"
    Write-Host ""
} else {
    Write-Host "ERROR: Failed to create scheduled task." -ForegroundColor Red
    exit 1
}