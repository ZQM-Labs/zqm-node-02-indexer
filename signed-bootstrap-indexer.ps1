<#
.SYNOPSIS
  Signed bootstrap for indexer service auto-start.
  Used by scheduled tasks in trusted-publisher environments.
#>

[CmdletBinding()]
param()

$PythonExe = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Error "Python not found in PATH."
    exit 1
}
$script = Join-Path $wd 'app.py'

if (-not (Test-Path $python)) {
    Write-Error "Python not found: $python"
    exit 1
}

Push-Location $wd
try {
    & $python $script
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

# SIG # Begin signature block
# MIIGCQYJKoZIhvcNAQcCoIIF+jCCBfYCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU7KFNnV6iUco8BnywlCSv8QJj
# qaCgggNwMIIDbDCCAlSgAwIBAgIQWrtZQqJyPqhFWG7K771CQjANBgkqhkiG9w0B
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
# CQQxFgQUI8XOu23KiIslrKPGzqaZllFVPdUwDQYJKoZIhvcNAQEBBQAEggEAOs1m
# RhewAV+So4kr/9CkRGsMR0s7cQkLjm6zmPl0j2qRe+nlQXQLzUrX49tWCxBp1vwa
# 0kj1lKR4harf23ZqQWdpNAmuK+wn8BVWYB0aH/gkQiwBFn9WJwK4kuhegUOMK/4Z
# mCBoHJjx5dDPRShna85mcZyIlEdiUrHQ/obeXuzGziCCHhBuquOg9//KdEgJN3R1
# d77B58wmhS+XRoLhCxXh5Q1+fAGEAfzVzmKCbzLB/d22bQ4cUgVrSddm9BlQ9gX0
# R4V+aOIfYbYZgM7qOFtvTp2GY7uBzyq9DT4yzkZD4GTl6R88vYlM44tMbXdcXp7J
# 0TpJfmPTbAi5PcUGOg==
# SIG # End signature block
