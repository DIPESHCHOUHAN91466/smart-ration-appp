<#
.SYNOPSIS
  Stop the local Smart Ration development servers (ports 5173, 5188, 8000, 8001).

.DESCRIPTION
  Only processes LISTENING on those four ports are stopped; it lists them and asks first
  (use -Yes to skip the question). MySQL and its data are never touched.

.EXAMPLE
  .\scripts\development\stop-all.ps1
  .\scripts\development\stop-all.ps1 -Yes
#>
param([switch]$Yes)
$ports = @{ 5173 = "Frontend"; 5188 = "C# API"; 8000 = "Python API"; 8001 = "AI service" }

$found = foreach ($port in $ports.Keys) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -Unique OwningProcess |
        ForEach-Object {
            $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($process) { [pscustomobject]@{ Service = $ports[$port]; Port = $port; Pid = $process.Id; Process = $process.ProcessName } }
        }
}

if (-not $found) { Write-Host "No Smart Ration development servers are running."; exit 0 }
$found | Sort-Object Port | Format-Table -AutoSize

if (-not $Yes) {
    $answer = Read-Host "Stop these processes? (y/N)"
    if ($answer -notin @("y", "Y", "yes")) { Write-Host "Nothing stopped."; exit 0 }
}
$found | ForEach-Object { Stop-Process -Id $_.Pid -ErrorAction SilentlyContinue }
Write-Host "Stopped." -ForegroundColor Green
