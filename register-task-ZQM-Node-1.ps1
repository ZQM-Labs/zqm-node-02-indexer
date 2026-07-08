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
# SIG # Begin signature block
# MIIF7wYJKoZIhvcNAQcCoIIF4DCCBdwCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCBxLjBXWir0T0bC
# Nj1XTZqF19xgofX9hGUGJkkMXQ8FRaCCA0YwggNCMIICKqADAgECAhAbD5NruMV9
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
# LwYJKoZIhvcNAQkEMSIEIMnMDeN6LUjux/uah1q0IcNfLEGRK7ZVUPsjCSuqyk7V
# MA0GCSqGSIb3DQEBAQUABIIBADdcNjm9gcmIP5uqWUwCAJLfJ5tI4MpP0FMOjUCt
# oDb8lS+CjUN8G6Njf0qTfia586JOwsA03w0+zGikZgwCB97wbSW4sUR2ZFtyCF6V
# 7CRmCDSzVf8bzanYeqQXQfpI6tFXu3Xo9yvDb04HHvOUo4BLoFc5guKZBILmzG5I
# j6vKpvzz8pY37V874zUS5iVNXw276BruNsiqkqiqLT96mN9lfZQiZFZDsu9krhKP
# qKGDlLKPGIKGGVAanOUaV8TxNnF3bLeLiDrzIHXGyVa+XbkIIxaE+uPHnIvjmbf+
# +rxbjuI4pnpezKcCG7jtj6sLmAgmkNOLZOnZaKXmg3Fvskw=
# SIG # End signature block
