<#
.SYNOPSIS
  Check every Smart Ration component and print one line each. Read-only.

.DESCRIPTION
  Frontend (:5173), Python API /health and /ready (:8000), C# API /api/health (:5188),
  AI service /health (:8001), and the MySQL schema via scripts/verify_database.py.
  Exit code 0 when everything is healthy, 1 otherwise.
#>
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$failures = 0

function Show([string]$Name, [bool]$Ok, [string]$Detail) {
    $mark = if ($Ok) { "OK  " } else { "FAIL" }
    $color = if ($Ok) { "Green" } else { "Red" }
    Write-Host ("{0}  {1,-22} {2}" -f $mark, $Name, $Detail) -ForegroundColor $color
    if (-not $Ok) { $script:failures++ }
}

function Probe([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return @{ Status = [int]$response.StatusCode; Body = $response.Content }
    } catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        return @{ Status = $status; Body = "" }
    }
}

$frontend = Probe "http://localhost:5173/"
Show "Frontend :5173" ($frontend.Status -eq 200) "HTTP $($frontend.Status)"

$health = Probe "http://localhost:8000/health"
$detail = "HTTP $($health.Status)"
if ($health.Body) {
    $h = $health.Body | ConvertFrom-Json
    $detail = "status=$($h.status) database=$($h.database) legacyApi=$($h.legacyApi) aiService=$($h.aiService) chatbot=$($h.chatbot) dataMode=$($h.dataMode)"
}
Show "Python API :8000" ($health.Status -eq 200 -and $health.Body -match '"status":"healthy"') $detail

$ready = Probe "http://localhost:8000/ready"
Show "Ready for traffic" ($ready.Status -eq 200) "HTTP $($ready.Status) /ready"

$legacy = Probe "http://localhost:5188/api/health"
Show "C# API :5188" ($legacy.Status -eq 200) "HTTP $($legacy.Status)"

$ai = Probe "http://localhost:8001/health"
Show "AI service :8001" ($ai.Status -eq 200) "HTTP $($ai.Status)"

$python = Join-Path $root "backend\SmartRation.Python\.venv\Scripts\python.exe"
if (Test-Path $python) {
    Push-Location (Join-Path $root "backend\SmartRation.Python")
    $output = & $python scripts\verify_database.py 2>&1 | Select-Object -Last 1
    Pop-Location
    Show "MySQL schema + data" ($output -match "PASSED") "$output"
} else {
    Show "MySQL schema + data" $false "Python backend not set up"
}

Write-Host ""
if ($failures -eq 0) { Write-Host "All components healthy." -ForegroundColor Green; exit 0 }
Write-Host "$failures check(s) failed. See docs\TROUBLESHOOTING.md." -ForegroundColor Red
exit 1
