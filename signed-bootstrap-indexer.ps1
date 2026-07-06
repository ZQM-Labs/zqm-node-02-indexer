<#
.SYNOPSIS
  Signed bootstrap for indexer service auto-start.
  Used by scheduled tasks in trusted-publisher environments.
#>

[CmdletBinding()]
param()

$python = 'C:\Users\zqmco\AppData\Local\Programs\Python\Python312\pythonw.exe'
$script = 'C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer\app.py'
$wd     = 'C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer'

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
# MIIFnQYJKoZIhvcNAQcCoIIFjjCCBYoCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUoQpqew77vLQh/SDKv/zb4TAC
# Hj2gggMoMIIDJDCCAgygAwIBAgIQQHi/y5WTA7pM4DU6y+c22zANBgkqhkiG9w0B
# AQsFADAqMSgwJgYDVQQDDB9aUU0gTG9jYWxob3N0IFRydXN0ZWQgUHVibGlzaGVy
# MB4XDTI2MDcwNTE3NTgyNFoXDTMxMDcwNTE4MDgyNFowKjEoMCYGA1UEAwwfWlFN
# IExvY2FsaG9zdCBUcnVzdGVkIFB1Ymxpc2hlcjCCASIwDQYJKoZIhvcNAQEBBQAD
# ggEPADCCAQoCggEBAOMe5PzqHjT+nkgArJPP6FwKAOJgXBQ05vV+upxtZLlfrVFA
# yRvP5JXNOGaZhWSoCOlff7WsrsUXkqOTrU+tggMCEJPQgJhl8vaQ0VVb5fGjXjdX
# fnuYeZ0EnZw+AO9rc3fjPot/A1eUN665M/b/Q/FJirE7KpYgz81zGeRFkEtQTt3e
# lziEZBgxWGBO1niHcxV5khmIxr81rW0x4L0s+qDW7YLbjlRWSwVa4xxR4J6/HS0B
# pNIni+MXDsBbMjLC9yDackZ3D4Ey0E7IEYB4fT+MwJGCi8AW95D3PVIpjpF3T/oM
# 1C04urgNtFzzHbYauAjhEEhZP/ccpELUgjptQCkCAwEAAaNGMEQwDgYDVR0PAQH/
# BAQDAgeAMBMGA1UdJQQMMAoGCCsGAQUFBwMDMB0GA1UdDgQWBBQlICKnD2E/Q+UF
# CAU94kNocQ5SxjANBgkqhkiG9w0BAQsFAAOCAQEAZJmrzwe6Pj7jYC8dA8OUoh2d
# 1xQK7kYCVnp9Jk3ggsp5j/vR/e0h/FC4O8jip+dz2jYC90irefIB07Aqg0qekEEQ
# Jiz2ran75dRRb9qBXyqhRKEsaLTsfvt8ila24atwpHOakkvIKLa3KNNLeLTmI2v0
# DVySWtKJDP8hQCpaDz/MO6qsenPQx7oDSxNcKDqcBwEec71ImZjugi031b0uWRdo
# maThP4EDkZy83nTZlhdk/7iSC/dce6hzlnJ93eZPaKfEJ5PxUpgt1mvySDTksYzD
# p0CLHgVG5rNRXulj98zWLvm5to9nxlR3+wafXGfarrWhRfd/hYd5Q8n2fopKjTGC
# Ad8wggHbAgEBMD4wKjEoMCYGA1UEAwwfWlFNIExvY2FsaG9zdCBUcnVzdGVkIFB1
# Ymxpc2hlcgIQQHi/y5WTA7pM4DU6y+c22zAJBgUrDgMCGgUAoHgwGAYKKwYBBAGC
# NwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0BCQMxDAYKKwYBBAGCNwIBBDAcBgor
# BgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAjBgkqhkiG9w0BCQQxFgQU8pR4Bo+o
# Oug/5j1chNfoZicMcI8wDQYJKoZIhvcNAQEBBQAEggEAq/sQlDTcZWaphZDWin1R
# 80pX47BjdUp5JV0PX35EgisEMDYFN1uu2b3CR6HPRiZ7WVjz89Fpn2lxS2p9ymVQ
# aLJG3bePyF4XhpksVbcbz7oAfbMBpKd4BaVtoZ6BztKtK1Z0l8r9BIsruV1cbIL+
# Z/12FBlpEA5XbTlkvcRa9J4oJ7MjPa6dJVxdl9bOeyKtG4IEy3J4MCLX7eTEnJ6I
# mwQTwXostdw+ptd3gpewVNXAyVeTAlRd/VKWXU62ruh1FMS1n4rsWyfZsNM9+2/h
# moZJHBY8ZrOJE5eu7xGF/zbtR29vI3Db6X6LGI6rN/URCeUB7xLCDZiBGSGHMCL/
# CA==
# SIG # End signature block
