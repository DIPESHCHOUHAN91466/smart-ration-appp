<#
.SYNOPSIS
  Start every Smart Ration service for local development, each in its own window.

.DESCRIPTION
  C# API (:5188) → AI service (:8001) → Python API (:8000, what the frontend calls) → frontend (:5173).
  A service whose port is already in use is skipped (it's probably already running).
  MySQL must already be running (Windows service MySQL80). Nothing is deleted or reset.

.EXAMPLE
  .\scripts\development\start-all.ps1
#>
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-DevService([string]$Name, [int]$Port, [string]$Directory, [string]$Command) {
    if (Test-Port $Port) {
        Write-Host ("  {0,-12} :{1}  already running - skipped" -f $Name, $Port) -ForegroundColor DarkGray
        return
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Smart Ration - $Name'; Set-Location '$Directory'; $Command" | Out-Null
    Write-Host ("  {0,-12} :{1}  starting" -f $Name, $Port) -ForegroundColor Green
}

$mysql = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if ($mysql -and $mysql.Status -ne "Running") {
    Write-Warning "MySQL80 service is $($mysql.Status). Start it first (services.msc or 'Start-Service MySQL80' as administrator)."
}

Write-Host "Starting Smart Ration services..." -ForegroundColor Cyan
Start-DevService "C# API" 5188 $root "dotnet run --project backend\SmartRation.Api --launch-profile http"

$aiPython = Join-Path $root "backend\SmartRation.AI\.venv\Scripts\python.exe"
if (Test-Path $aiPython) {
    Start-DevService "AI service" 8001 (Join-Path $root "backend\SmartRation.AI") ".venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --host 127.0.0.1 --port 8001"
} else {
    Write-Host "  AI service   :8001  not set up (backend\SmartRation.AI\README.md) - AI panels will show 'unavailable'" -ForegroundColor Yellow
}

$pyPython = Join-Path $root "backend\SmartRation.Python\.venv\Scripts\python.exe"
if (Test-Path $pyPython) {
    Start-DevService "Python API" 8000 (Join-Path $root "backend\SmartRation.Python") ".venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000"
} else {
    Write-Warning "Python API not set up (backend\SmartRation.Python\README.md). The frontend needs it on :8000."
}

$frontend = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "  Installing frontend dependencies (first run)..." -ForegroundColor Yellow
    Push-Location $frontend; npm install; Pop-Location
}
Start-DevService "Frontend" 5173 $frontend "npm run dev"

Write-Host ""
Write-Host "Open http://localhost:5173  (status page: http://localhost:5173/status)" -ForegroundColor Cyan
Write-Host "Check everything with: .\scripts\development\health-check.ps1" -ForegroundColor Cyan
