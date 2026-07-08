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
$PythonExe = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python interpreter not found in PATH." -ForegroundColor Red
    exit 1
}
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
# SIG # Begin signature block
# MIIF7wYJKoZIhvcNAQcCoIIF4DCCBdwCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCAEXBxsJgY9ezVG
# ybI52li+0qfDcv1DJw8TFe7Zzz0wSKCCA0YwggNCMIICKqADAgECAhAbD5NruMV9
# n0Q0PL3odUenMA0GCSqGSIb3DQEBCwUAMDkxNzA1BgNVBAMMLkFsZXggWmVsZW5z
# a2lcLCBHSVNQLCBFPXpxbWNvbXB1dGluZ0BnbWFpbC5jb20wHhcNMjYwNzA4MjE0
# MjUwWhcNMjcwNzA4MjIwMjUwWjA5MTcwNQYDVQQDDC5BbGV4IFplbGVuc2tpXCwg
# R0lTUCwgRT16cW1jb21wdXRpbmdAZ21haWwuY29tMIIBIjANBgkqhkiG9w0BAQEF
# AAOCAQ8AMIIBCgKCAQEAnPgyTaTlR6cjFmVc84KCMcd+KwubsJqC9MAizBr6sd6I
# 1tknamkkClQmnhw666vosh1fjabkdfhFYkZOEJjGteXXW3MdHTd/RF3GJ43Bh0af
# i30ss84EFXjtKPtZ/i5xO3v72B8rCYmNWO5pUOlPE4uGZditxgzfyn+seezoHhUc
# DiHtwaEKrslirKGzsokK5T7ly7G+0QAYc/nVSPrhiT7cNbbgHc8WEbnwYe9Nxe30
# ymZVJjZnYtZpKL6T76AwHzVva6nVbmkLUIcO+3SRCzrIljiX8aJ3QCGispMUHnWW
# SJnxNtVgNbhQ1b+PRewB5Lz/uAsJ82v8Gu4FfPu22QIDAQABo0YwRDAOBgNVHQ8B
# Af8EBAMCB4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwHQYDVR0OBBYEFAPLoyIfPLFH
# n36hJBuv3pQLHAAvMA0GCSqGSIb3DQEBCwUAA4IBAQAs2B/3n41d3RlN9jaYztbh
# m0Cu5A+iXIH8X8Njff3mhGg9iS0mF8QkobS40b/TqYFnjWO+UQ1i5zw0SbuulwZA
# BNBbKnv1qxiogmbSMfSclb2uei5EgeHGykjCw+P6incHimou3fFCt5C3Aw8pU2Xf
# a2NxC1MD5zjPNtZMUUgyjuPB3Qt/bCcY/H9oDt011KzMpMJAZcs1sZ9iwFuG5ITJ
# ShBNEv1H/nuh0PNTE/J6ks7shxbgo19DsIEd+NnADE8OYetgZmA/qmQ1zcXE5eWx
# bqrTTg8HHJElf+ADCdbDrv9bZBnBFih5J0Msf38ssEOABtWK4R/1huqQODfAem4M
# MYIB/zCCAfsCAQEwTTA5MTcwNQYDVQQDDC5BbGV4IFplbGVuc2tpXCwgR0lTUCwg
# RT16cW1jb21wdXRpbmdAZ21haWwuY29tAhAbD5NruMV9n0Q0PL3odUenMA0GCWCG
# SAFlAwQCAQUAoIGEMBgGCisGAQQBgjcCAQwxCjAIoAKAAKECgAAwGQYJKoZIhvcN
# AQkDMQwGCisGAQQBgjcCAQQwHAYKKwYBBAGCNwIBCzEOMAwGCisGAQQBgjcCARUw
# LwYJKoZIhvcNAQkEMSIEIHGnsSQaw5W7G7vF1DGZH7neLaeDRbJecm5MD+23WmrA
# MA0GCSqGSIb3DQEBAQUABIIBAClg+s9YprvJRIYs2DXTsgNOlRrF/8r3CaDDkdvW
# THP20XvV1eX++Mmp3J3fdUu1Ee9WtRBGRdJf3fE/HC5/ihurj64az3RMqziqsFZC
# AQYeIt2GFuq02QYJ2V+ehHhF8GQhbMFe0tO3WApk/DoJmJITJ0tokEALAcaBJZLi
# 1NeBSXIbIuwACw1JE4C0YqjJR7GGtAkyov8+6gs9o5uhqES5MImvox5fap/0qzJ4
# DEJCsYmLykmYa+XQfAuCx1f8DFAsg/O7VTA9PJE4JIzM3ulBe0zn3BecvHFdVVnE
# dsoA+l+MgPHBWDPH5gJm161YWBIATDj7RYYEqn3eU4og1rI=
# SIG # End signature block
