<#
.SYNOPSIS
  Deploy schema and seed data to Azure Database for MySQL Flexible Server.

.DESCRIPTION
  Connects to Azure Database for MySQL Flexible Server, applies all Alembic
  migrations (revisions 0001 through 0007), and seeds synthetic reference data.

.PARAMETER Server
  The Azure MySQL host. Default: smartration-ai.mysql.database.azure.com

.PARAMETER AdminUser
  The Azure administrator username. Default: airationmitrahsd2c

.PARAMETER Password
  The administrator password. If omitted, will be prompted securely.

.EXAMPLE
  .\scripts\database\deploy-azure-db.ps1
#>
param(
    [string]$Server = "smartration-ai.mysql.database.azure.com",
    [string]$AdminUser = "airationmitrahsd2c",
    [string]$Database = "smartration",
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Smart Ration — Azure MySQL Flexible Server Deployment    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Target Server : $Server" -ForegroundColor Yellow
Write-Host "Admin User    : $AdminUser" -ForegroundColor Yellow
Write-Host "Database      : $Database" -ForegroundColor Yellow
Write-Host ""

if ([string]::IsNullOrWhiteSpace($Password)) {
    $securePass = Read-Host "Enter Azure MySQL password for user '$AdminUser'" -AsSecureString
    $Password = [System.Net.NetworkCredential]::new("", $securePass).Password
}

$encodedPassword = [System.Uri]::EscapeDataString($Password)
$backendDir = Resolve-Path (Join-Path $PSScriptRoot "..\..\backend\SmartRation")
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at: $pythonExe"
}

# Construct connection URL for admin/migrator
$dbUrl = "mysql+pymysql://${AdminUser}:${encodedPassword}@${Server}:3306/${Database}?charset=utf8mb4"

Write-Host "[1/3] Checking and creating database '$Database' if needed..." -ForegroundColor Cyan

$createDbScript = @"
import pymysql, sys
try:
    conn = pymysql.connect(host='$Server', user='$AdminUser', password='$Password', port=3306)
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS \`$Database\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    conn.close()
    print("Database '$Database' ready.")
except Exception as e:
    print(f"Error creating database: {e}", file=sys.stderr)
    sys.exit(1)
"@

& $pythonExe -c $createDbScript
if ($LASTEXITCODE -ne 0) {
    throw "Failed to ensure database exists on Azure MySQL."
}

Write-Host "[2/3] Running Alembic migrations and synthetic seeder on Azure MySQL..." -ForegroundColor Cyan
Push-Location $backendDir
try {
    $env:DATABASE_URL = $dbUrl
    $env:MIGRATION_DATABASE_URL = $dbUrl
    $env:DATA_MODE = "synthetic"

    & $pythonExe scripts\setup_database.py --seed
    if ($LASTEXITCODE -ne 0) {
        throw "setup_database.py failed with exit code $LASTEXITCODE"
    }

    Write-Host "[3/3] Verifying database schema and tables on Azure MySQL..." -ForegroundColor Cyan
    & $pythonExe scripts\verify_database.py
    if ($LASTEXITCODE -ne 0) {
        throw "verify_database.py reported schema validation errors."
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "SUCCESS: Azure Database for MySQL Flexible Server is fully initialized and seeded!" -ForegroundColor Green
Write-Host "All 27 tables and Alembic migrations have been deployed." -ForegroundColor Green
