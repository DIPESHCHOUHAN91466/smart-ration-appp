<#
.SYNOPSIS
  Start every Smart Ration service for local development, each in its own window.

.DESCRIPTION
  C# API (:5188) → AI service (:8001) → Python API (:8000, what the frontend calls) → frontend (:5173).
  A service whose port is already in use is skipped (it's probably already running).
  After starting, it waits (up to -TimeoutSeconds, default 120) for each port and prints
  SERVICE FAILED / REASON / COMMAND for any service that didn't come up; exit code 1 in that case.
  MySQL must already be running (Windows service MySQL80). Nothing is deleted or reset.

.EXAMPLE
  .\scripts\development\start-all.ps1
#>
param([int]$TimeoutSeconds = 120)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

# Names of the processes listening on a port (e.g. "python", "dotnet", "com.docker.backend").
function Get-PortOwners([int]$Port) {
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName } |
        Where-Object { $_ } | Sort-Object -Unique)
}

$started = New-Object System.Collections.Generic.List[object]
$script:conflicts = 0

function Start-DevService([string]$Name, [int]$Port, [string]$Directory, [string]$Command, [string]$Expected) {
    if (Test-Port $Port) {
        # A port can be taken by another program (e.g. a Docker container publishing the same port):
        # then "already running" would be wrong, and requests to "localhost" may reach that program.
        $owners = Get-PortOwners $Port
        $foreign = @($owners | Where-Object { $_ -notmatch $Expected })
        if ($foreign.Count -eq 0) {
            Write-Host ("  {0,-12} :{1}  already running - skipped" -f $Name, $Port) -ForegroundColor DarkGray
        } elseif ($foreign.Count -lt $owners.Count) {
            Write-Host ("  {0,-12} :{1}  already running - skipped. WARNING: also used by {2}; 'localhost' requests may reach it instead" -f $Name, $Port, ($foreign -join ", ")) -ForegroundColor Yellow
        } else {
            $script:conflicts++
            Write-Host "SERVICE FAILED: $Name" -ForegroundColor Red
            Write-Host "REASON:         port $Port is used by another program: $($foreign -join ', ') (stop it, e.g. its Docker container)" -ForegroundColor Red
            Write-Host "COMMAND:        cd '$Directory'; $Command" -ForegroundColor Red
        }
        return
    }
    # -NoExit keeps the window open, so a crash leaves its error message visible there.
    $process = Start-Process powershell -PassThru -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Smart Ration - $Name'; Set-Location '$Directory'; $Command"
    $started.Add([pscustomobject]@{ Name = $Name; Port = $Port; Directory = $Directory; Command = $Command; Process = $process })
    Write-Host ("  {0,-12} :{1}  starting" -f $Name, $Port) -ForegroundColor Green
}

$mysql = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if ($mysql -and $mysql.Status -ne "Running") {
    Write-Warning "MySQL80 service is $($mysql.Status). Start it first (services.msc or 'Start-Service MySQL80' as administrator)."
}

Write-Host "Starting Smart Ration services..." -ForegroundColor Cyan
Start-DevService "C# API" 5188 $root "dotnet run --project backend\SmartRation.Api --launch-profile http" "^(dotnet|SmartRation\.Api)$"

$aiPython = Join-Path $root "backend\SmartRation.AI\.venv\Scripts\python.exe"
if (Test-Path $aiPython) {
    Start-DevService "AI service" 8001 (Join-Path $root "backend\SmartRation.AI") ".venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --host 127.0.0.1 --port 8001" "^python"
} else {
    Write-Host "  AI service   :8001  not set up (backend\SmartRation.AI\README.md) - AI panels will show 'unavailable'" -ForegroundColor Yellow
}

$pyPython = Join-Path $root "backend\SmartRation.Python\.venv\Scripts\python.exe"
if (Test-Path $pyPython) {
    Start-DevService "Python API" 8000 (Join-Path $root "backend\SmartRation.Python") ".venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000" "^python"
} else {
    Write-Warning "Python API not set up (backend\SmartRation.Python\README.md). The frontend needs it on :8000."
}

$frontend = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "  Installing frontend dependencies (first run)..." -ForegroundColor Yellow
    Push-Location $frontend; npm install; Pop-Location
}
Start-DevService "Frontend" 5173 $frontend "npm run dev" "^node"

if ($started.Count) {
    Write-Host ""
    Write-Host "Waiting for the services to listen (up to $TimeoutSeconds s)..." -ForegroundColor Cyan
}
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$failed = $script:conflicts
foreach ($service in $started) {
    while (-not (Test-Port $service.Port) -and (Get-Date) -lt $deadline -and -not $service.Process.HasExited) { Start-Sleep -Milliseconds 500 }
    if (Test-Port $service.Port) {
        Write-Host ("  {0,-12} :{1}  running" -f $service.Name, $service.Port) -ForegroundColor Green
        continue
    }
    $failed++
    $reason = if ($service.Process.HasExited) { "its window closed (exit code $($service.Process.ExitCode))" } else { "port $($service.Port) not listening after $TimeoutSeconds s - read the error in the 'Smart Ration - $($service.Name)' window" }
    Write-Host "SERVICE FAILED: $($service.Name)" -ForegroundColor Red
    Write-Host "REASON:         $reason" -ForegroundColor Red
    Write-Host "COMMAND:        cd '$($service.Directory)'; $($service.Command)" -ForegroundColor Red
}

Write-Host ""
if ($failed) {
    Write-Host "$failed service(s) failed to start. See docs\development\TROUBLESHOOTING.md." -ForegroundColor Red
    exit 1
}
Write-Host "Open http://localhost:5173  (status page: http://localhost:5173/status)" -ForegroundColor Cyan
Write-Host "Check everything with: .\scripts\development\health-check.ps1" -ForegroundColor Cyan
