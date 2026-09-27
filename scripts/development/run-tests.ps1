<#
.SYNOPSIS
  Run every automated test suite and print a summary. Read-only for real data.

.DESCRIPTION
  Python backend (pytest), chatbot evaluation, AI service (pytest), C# (dotnet test on SmartRation.sln),
  frontend (ESLint, Vitest, production build) and a read-only database health check.
  -MySql also runs the MySQL suite (146 tests) against smartration_test (never the real database):
  it builds TEST_DATABASE_URL from backend\SmartRation\.env with the database name changed.
  -Quick skips the C# build, the frontend and the database check (fastest feedback while working on Python).
  -E2E also runs the Playwright end-to-end tests (the stack must already be running: start-all.ps1).
  Works from any current directory.

.EXAMPLE
  .\scripts\development\run-tests.ps1
  .\scripts\development\run-tests.ps1 -MySql
#>
param([switch]$MySql, [switch]$Quick, [switch]$E2E)
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

$py = Join-Path $root "backend\SmartRation"
Run "Python backend" $py { & .venv\Scripts\python -m pytest -p no:warnings }
Run "Chatbot evaluation" $py { & .venv\Scripts\python -m app.chatbot.evaluate }

if ($MySql) {
    $url = & "$py\.venv\Scripts\python" "$py\scripts\test_database_url.py"   # password stays in this variable only
    if ($LASTEXITCODE -ne 0 -or -not $url) { throw "Could not build TEST_DATABASE_URL from backend\SmartRation\.env" }
    $env:TEST_DATABASE_URL = $url
    Run "MySQL suite (smartration_test)" $py { & .venv\Scripts\python -m pytest tests/mysql_suite -p no:warnings }
    Run "Root MySQL tests (tests/mysql)" $root { & "$py\.venv\Scripts\python" -m pytest tests/mysql -p no:warnings }
    Remove-Item Env:TEST_DATABASE_URL
}

Run "AI service" (Join-Path $root "backend\SmartRation.AI") { & .venv\Scripts\python -m pytest -p no:warnings }

if (-not $Quick) {
    # Release configuration: a running API (Debug build) locks its own .exe, which would break the build.
    Run "C# API (SmartRation.sln)" $root { dotnet test SmartRation.sln -c Release --nologo -v q }
    $frontend = Join-Path $root "frontend"
    Run "Frontend lint (ESLint)" $frontend { npm run lint --silent }
    Run "Frontend (Vitest)" $frontend { npm test --silent }
    Run "Frontend build" $frontend { npm run build --silent }
    Run "Database health (smartration)" $py { & .venv\Scripts\python scripts\verify_database.py }
}

if ($E2E) {
    Run "End-to-end (Playwright)" (Join-Path $root "frontend") { npm run test:e2e --silent }
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize
if ($results.Result -contains "FAIL") { exit 1 } else { exit 0 }
