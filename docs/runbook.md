# ZQM-Node-2 — Index / Runbook

Repo: `zqm-node-02-indexer`
Node: `192.168.1.21` — `ZQM-Node-2.lan` (this machine)
MAC: `E8:65:38:ED:95:AD` (MediaTek)
Updated: `2026-07-06`

## Authentication

- Account `zqmcomputing` is local admin-equivalent on Node-2.
- Shared credential accepted for WMI/CIM and SMB sessions without explicit password re-entry from local admin context.
- Password reuse: same shared credential as Node-1.

## Open TCP ports

- `135/tcp` epmap
- `139/tcp` netbios-ssn
- `445/tcp` microsoft-ds

## Identity

- Hostname: `ZQM-NODE-2`
- Computer SID / UUID: `FF4C5CB1-62B6-47EC-B89A-FC5CEED02D9E`
- Workgroup: `WORKGROUP`
- OS: Windows 11 Pro `10.0.26200` / build `26200`
- Enrolled user: `ZQM-Node-2\zqmco` (`Alex Zelenski`)
- System: LENOVO `82WS` / Legion Pro 7 16ARX8H / 64 GiB / 32 logical CPUs
- BIOS `LPCN65WW` (2026-03-25)
- Wi-Fi: `RZ616 Wi-Fi 6E`, IPv4 `192.168.1.21/24`, GW `192.168.1.1`

## Broadcasts

- Same discovery set as Node-1.

## Remote access status

- WinRM: installed but not configured on this host. Run `Enable-PSRemoting -Force` and TrustedHosts setup if cross-node remote management is desired.
- RDP: not confirmed listening externally.

## Change log

- 2026-07-06 — initial enumeration, WMI inventory, credential matrix added.
