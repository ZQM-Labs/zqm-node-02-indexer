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
# MIIGCQYJKoZIhvcNAQcCoIIF+jCCBfYCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUry/eDjP/p2wS1gBrPsnkEK6z
# G1egggNwMIIDbDCCAlSgAwIBAgIQWrtZQqJyPqhFWG7K771CQjANBgkqhkiG9w0B
# AQUFADBOMSUwIwYJKoZIhvcNAQkBFhZ6cW1jb21wdXRpbmdAZ21haWwuY29tMQ0w
# CwYDVQQKDARHSVNQMRYwFAYDVQQDDA1BbGV4IFplbGVuc2tpMB4XDTI2MDcwODE4
# MjEyNFoXDTMxMDcwODE4MzEyNFowTjElMCMGCSqGSIb3DQEJARYWenFtY29tcHV0
# aW5nQGdtYWlsLmNvbTENMAsGA1UECgwER0lTUDEWMBQGA1UEAwwNQWxleCBaZWxl
# bnNraTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJeQSZT74KdFYkD1
# E/0viBoiz5PY/dXu5I4mQirwH1IGBZPRoyu0JyJ/gyxk6Hk2T0eGQrDwrR9z9Sn2
# wPWp6qUdrXjlQFnyq6pzs6593R9QsKaQ66IwSrZfZ1fsvvABKsUiJ64NoFuWNAQW
# XuzUpPzrlBtlJa6iOiUOGAWS4dxeK5WokGM0pF196fgWEXJNc8PWCxba/9HBcEWX
# v+YKytRx1mFVNkcmlMkDFoVCIxINGnzPiYzWr6gtF0pyBsq61Z/AOMiz9icpNUCp
# xFRUmX5yppQBHZfZxDRDbbkGpkDrWsB3h3LuiuhJYj6dSbmzjt+x7bQ/vM0Kqpb9
# NSYjBtkCAwEAAaNGMEQwDgYDVR0PAQH/BAQDAgeAMBMGA1UdJQQMMAoGCCsGAQUF
# BwMDMB0GA1UdDgQWBBTGnmIIMh/gvLzipxfXFVJbXn3yxzANBgkqhkiG9w0BAQUF
# AAOCAQEANliRLvkm53YjnKv1ybg6SRzAbhppfspw0ZrWP68uvz98MEm9w9Sl5PbA
# vfrqn39SEfWkPliV08ilWyAabHhUvw1MCDvinJp9SLBqleAI2qpWdLFxMUJZV4hq
# 5jhlyM5n/Gd443JgRlILu02hejBHHbPNw6ivv2sfy4JWLEDFJbHlHaj5ZjjwOSen
# 9J1jmX/592Hz4xWu8cEmZeW/4DvXr4pLMbaKlIrZ7XGtTB+AAcNutg7/vIHf8UBd
# QN8A1Z9kzARgo2beNPAO6VU6/fMcq5aB7/9EfToPvOgZGwiwIfu5C7oGl6YbMQP3
# cggqNFN0sp1dIwv5dSANMKBoP02VYjGCAgMwggH/AgEBMGIwTjElMCMGCSqGSIb3
# DQEJARYWenFtY29tcHV0aW5nQGdtYWlsLmNvbTENMAsGA1UECgwER0lTUDEWMBQG
# A1UEAwwNQWxleCBaZWxlbnNraQIQWrtZQqJyPqhFWG7K771CQjAJBgUrDgMCGgUA
# oHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0BCQMxDAYKKwYB
# BAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAjBgkqhkiG9w0B
# CQQxFgQUdgOX+yZXNK9SI21UW3ths3Qgr6IwDQYJKoZIhvcNAQEBBQAEggEATXFc
# 7yRGll8NunpZM+7o0wjDFbamVN9jl1+lN33X6pzf5jfyavEebfDHyBz2avvYHTgR
# +VY6jY3HfAj4Xzx/FGAv3FGix9Ou/kyEZMNQ6h0wdwGZ34k7/b7mvvtj14rT9MvH
# hki3IoNMek7WWrrlLnIK4C23T1YV71qK5hOus8nZyC/FDmb6k8okEuKjTpDRzaAZ
# 0t7o4Sy29PWJ3MTsKWmfTB9K9HBWy95bM/32b4xHItb8cAcSvh4UdaVPTeVgwaTs
# z2gQ8vEMXsU+HMiFHaEvz+85DvFttNfsgI1I7RQPlajFBwuY2j44+fkyX8fgFg5E
# Rpg/XlYRVDhBiTwiBQ==
# SIG # End signature block
