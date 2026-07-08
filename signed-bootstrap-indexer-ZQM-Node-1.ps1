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
# MIIF7wYJKoZIhvcNAQcCoIIF4DCCBdwCAQExDzANBglghkgBZQMEAgEFADB5Bgor
# BgEEAYI3AgEEoGswaTA0BgorBgEEAYI3AgEeMCYCAwEAAAQQH8w7YFlLCE63JNLG
# KX7zUQIBAAIBAAIBAAIBAAIBADAxMA0GCWCGSAFlAwQCAQUABCDrF7pIPuG+eW/I
# QtUVZVd5ZXNUXaZeK7B/+cYuFWgEE6CCA0YwggNCMIICKqADAgECAhAbD5NruMV9
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
# LwYJKoZIhvcNAQkEMSIEIIpa9VEFfkEpFqUZ5fF8VNCjBu5RjMKLOkXC+NzUVdeR
# MA0GCSqGSIb3DQEBAQUABIIBAINS4jaDAdEYy/24VQMk/v50S7iDhBxRfZsMSOjM
# PNZAUnTXx7nUg2pIRXvEzNFo4Wd/nKjdagLYqx/CSxU5kgqTbzb5bkRuCGrqzkIz
# bnd4HBHbVWalzHhWi1m1UhDQPbjHZ70MUE1NoSHotDaR2+jnYWMEpFJvTRc+2wuE
# zQa+P8L3t7WVTb7P8tTe9Zn/ikH6OZbtCHrbN1xewBV1lOHbVqsUVK/4hJkRHBuz
# qldohwmcWeoe8myb5AvBDPF/aZdrr1ZyZepRA/W+PsoOjyjcfcAFKotkhC+ehjac
# XefhtcfKjMbg66evG5Mil20uAlMcku7wA9UeErzjwbrDUhk=
# SIG # End signature block
