<#
.SYNOPSIS
  Create/adopt the database schema and load SYNTHETIC demo data. Non-destructive.

.DESCRIPTION
  Runs backend\SmartRation\scripts\setup_database.py --seed:
    - empty database  -> creates the schema, then seeds
    - existing schema -> verifies it, applies pending migrations
  Seed data (database\seeds\synthetic\*.json) is inserted into EMPTY tables only, so an existing
  database keeps all its rows. Refused unless DATA_MODE=synthetic.
  Demo users are created only if SEED_DEMO_PASSWORD is set (and only when there are no users).

.EXAMPLE
  $env:SEED_DEMO_PASSWORD = "<choose one>"   # optional
  .\scripts\database\seed-demo-data.ps1
#>
$ErrorActionPreference = "Stop"
$backend = Resolve-Path (Join-Path $PSScriptRoot "..\..\backend\SmartRation")
$python = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python backend not set up: see backend\SmartRation\README.md" }
Push-Location $backend
try { & $python scripts\setup_database.py --seed; exit $LASTEXITCODE } finally { Pop-Location }
