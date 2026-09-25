<#
.SYNOPSIS
  Run every automated test suite and print a summary. Read-only for real data.

.DESCRIPTION
  Python backend (pytest), chatbot evaluation, AI service (pytest), C# (dotnet test), frontend (Vitest).
  -MySql also runs the 122-test MySQL suite against smartration_test (never the real database):
  it builds TEST_DATABASE_URL from backend\SmartRation.Python\.env with the database name changed.
  -Quick skips the C# build and the frontend (fastest feedback while working on Python).

.EXAMPLE
  .\scripts\development\run-tests.ps1
  .\scripts\development\run-tests.ps1 -MySql
#>
param([switch]$MySql, [switch]$Quick)
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$results = New-Object System.Collections.Generic.List[object]

function Run([string]$Name, [string]$Directory, [scriptblock]$Command) {
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    Push-Location $Directory
    $watch = [Diagnostics.Stopwatch]::StartNew()
    & $Command
    $code = $LASTEXITCODE
    Pop-Location
    $results.Add([pscustomobject]@{ Suite = $Name; Result = $(if ($code -eq 0) { "PASS" } else { "FAIL" }); Seconds = [int]$watch.Elapsed.TotalSeconds })
}

$py = Join-Path $root "backend\SmartRation.Python"
Run "Python backend" $py { & .venv\Scripts\python -m pytest -p no:warnings }
Run "Chatbot evaluation" $py { & .venv\Scripts\python -m app.chatbot.evaluate }

if ($MySql) {
    $url = & "$py\.venv\Scripts\python" "$py\scripts\test_database_url.py"   # password stays in this variable only
    if ($LASTEXITCODE -ne 0 -or -not $url) { throw "Could not build TEST_DATABASE_URL from backend\SmartRation.Python\.env" }
    $env:TEST_DATABASE_URL = $url
    Run "MySQL suite (smartration_test)" $py { & .venv\Scripts\python -m pytest tests/mysql_suite -p no:warnings }
    Remove-Item Env:TEST_DATABASE_URL
}

Run "AI service" (Join-Path $root "backend\SmartRation.AI") { & .venv\Scripts\python -m pytest -p no:warnings }

if (-not $Quick) {
    # Release configuration: a running API (Debug build) locks its own .exe, which would break the build.
    Run "C# API" $root { dotnet test backend\SmartRation.Api.Tests\SmartRation.Api.Tests.csproj -c Release --nologo -v q }
    Run "Frontend (Vitest)" (Join-Path $root "frontend") { npm test --silent }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize
if ($results.Result -contains "FAIL") { exit 1 } else { exit 0 }
