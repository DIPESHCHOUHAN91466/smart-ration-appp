<#
.SYNOPSIS
  Smart Ration developer command: one entry point for everyday tasks. Run from anywhere.

.EXAMPLE
  .\sr.ps1 help
  .\sr.ps1 setup
  .\sr.ps1 run
  .\sr.ps1 test -MySql
  .\sr.ps1 synthetic --users 1000 --insert --bookings
#>
param(
    [Parameter(Position = 0)][string]$Command = "help",
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest
)
$root = $PSScriptRoot
$dev = Join-Path $root "scripts\development"
$py = Join-Path $root "backend\SmartRation.Python"
$pyExe = Join-Path $py ".venv\Scripts\python.exe"

function Script([string]$Name, [string[]]$Arguments = $Rest) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $dev $Name) @Arguments
    exit $LASTEXITCODE
}
function InDir([string]$Dir, [scriptblock]$Block) { Push-Location $Dir; try { & $Block } finally { Pop-Location } }
function Step([string]$Name, [scriptblock]$Block) {
    Write-Host "== $Name" -ForegroundColor Cyan
    & $Block
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $Name (exit code $LASTEXITCODE)" -ForegroundColor Red; exit $LASTEXITCODE }
}

switch ($Command.ToLowerInvariant()) {
    "setup"     { Script "setup.ps1" }                       # tools, venvs, packages, restore, .env templates
    "run"       { Script "start-all.ps1" }                   # all four services, each in its own window
    "stop"      { Script "stop-all.ps1" }
    "health"    { Script "health-check.ps1" }
    "audit"     { Script "audit-dependencies.ps1" }             # known vulnerabilities in every dependency
    "test"      { Script "run-tests.ps1" }                   # add -MySql / -Quick
    "e2e"       { InDir (Join-Path $root "frontend") { npm run test:e2e @Rest }; exit $LASTEXITCODE }
    "build" {
        Step "C# (SmartRation.sln, Release)" { InDir $root { dotnet build SmartRation.sln -c Release --nologo -v q } }
        Step "Frontend (vite build)" { InDir (Join-Path $root "frontend") { npm run build --silent } }
        Step "Python (import check)" { InDir $py { & $pyExe -c "import app.main" } }
        Write-Host "Build OK" -ForegroundColor Green
    }
    "lint" {
        Step "Python: ruff" { InDir $py { & $pyExe -m ruff check . } }
        Step "Python: mypy" { InDir $py { & $pyExe -m mypy } }
        Step "Frontend: ESLint" { InDir (Join-Path $root "frontend") { npm run lint --silent } }
        Write-Host "Lint OK" -ForegroundColor Green
    }
    "db" {
        $action = if ($Rest) { $Rest[0] } else { "verify" }
        switch ($action) {
            "verify" { InDir $py { & $pyExe scripts\verify_database.py }; exit $LASTEXITCODE }   # read-only
            "seed"   { Script "seed-demo-data.ps1" @() }                                           # empty tables only
            "schema" { InDir $py { & $pyExe scripts\export_schema_sql.py }; exit $LASTEXITCODE }  # regenerate database/schema
            default  { Write-Host "db verify | seed | schema" -ForegroundColor Yellow; exit 1 }
        }
    }
    "synthetic" { InDir $py { & $pyExe scripts\generate_test_data.py @Rest }; exit $LASTEXITCODE }   # --help for options
    "contracts" { InDir $py { & $pyExe scripts\export_openapi.py @Rest }; exit $LASTEXITCODE }       # --csharp http://localhost:5188
    "docker"    { InDir $root { docker build -f backend/SmartRation.Python/Dockerfile -t smartration-api:local . }; exit $LASTEXITCODE }
    default {
        Write-Host @"
Smart Ration developer commands (.\sr.ps1 <command>):

  setup                 first-time / refresh setup (virtualenvs, packages, dotnet restore, .env templates)
  run | stop            start / stop C# :5188, AI :8001, Python :8000, frontend :5173
  health                check tools, setup, services, ports and database  [PASS] [WARNING] [FAIL] [NOT CONFIGURED]
  audit                 known vulnerabilities in Python, npm and C# dependencies (needs internet)
  test [-MySql|-Quick]  every test suite + lint + build + database health
  e2e                   end-to-end browser tests (Playwright; the stack must be running)
  build                 C# (Release), frontend production build, Python import check
  lint                  ruff + mypy + ESLint
  db verify|seed|schema read-only database check | seed empty tables | regenerate database/schema SQL
  synthetic <options>   synthetic citizens, e.g. --users 1000 --insert --bookings --collections 0.5
  contracts [--csharp URL]  regenerate the API contracts in api/openapi
  docker                build the Python API container image
"@
        if ($Command -ne "help") { Write-Host "Unknown command '$Command'." -ForegroundColor Red; exit 1 }
    }
}
