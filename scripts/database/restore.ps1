<#
.SYNOPSIS
  Restore a Smart Ration backup made by backup.ps1. DESTRUCTIVE for the target database.

.DESCRIPTION
  1. Verifies the backup's SHA-256 checksum and completeness.
  2. Takes a fresh safety backup of the CURRENT database first (never lose the only copy).
  3. Restores the dump (it recreates every table it contains).
  Requires -Confirm RESTORE_SMARTRATION. Stop the API servers before restoring.

.EXAMPLE
  $env:SMARTRATION_DB_USER = "smartration_app"; $env:SMARTRATION_DB_PASSWORD = "<password>"
  .\scripts\database\restore.ps1 -BackupFile .\database\backups\smartration_20260924_101500.sql.gz -Confirm RESTORE_SMARTRATION
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$BackupFile,
    [Parameter(Mandatory)] [string]$Confirm,
    [string]$Database = "smartration",
    [string]$DbHost = "localhost",
    [int]$Port = 3306,
    [switch]$SkipSafetyBackup,
    [string]$MySqlBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin"
)
$ErrorActionPreference = "Stop"

if ($Confirm -ne "RESTORE_SMARTRATION") { throw "Refusing to restore: pass -Confirm RESTORE_SMARTRATION." }
$user = $env:SMARTRATION_DB_USER; $password = $env:SMARTRATION_DB_PASSWORD
if (-not $user -or -not $password) { throw "Set SMARTRATION_DB_USER and SMARTRATION_DB_PASSWORD first." }
if (-not (Test-Path $BackupFile)) { throw "Backup file not found: $BackupFile" }
$mysql = Join-Path $MySqlBin "mysql.exe"

# 1. Checksum
$shaFile = "$BackupFile.sha256"
if (Test-Path $shaFile) {
    $expected = (Get-Content $shaFile).Split(" ")[0]
    $actual = (Get-FileHash $BackupFile -Algorithm SHA256).Hash
    if ($expected -ne $actual) { throw "Checksum mismatch for $BackupFile; refusing to restore." }
} else { Write-Warning "No .sha256 file next to the backup; integrity not verified." }

# 2. Safety backup of the current state
if (-not $SkipSafetyBackup) {
    & (Join-Path $PSScriptRoot "backup.ps1") -Database $Database -DbHost $DbHost -Port $Port -MySqlBin $MySqlBin
}

# 3. Decompress to a temp file and restore
$sqlFile = [System.IO.Path]::GetTempFileName()
$optionFile = [System.IO.Path]::GetTempFileName()
try {
    if ($BackupFile.EndsWith(".gz")) {
        $in = [System.IO.File]::OpenRead((Resolve-Path $BackupFile))
        $gz = New-Object System.IO.Compression.GZipStream($in, [System.IO.Compression.CompressionMode]::Decompress)
        $out = [System.IO.File]::Create($sqlFile)
        try { $gz.CopyTo($out) } finally { $out.Dispose(); $gz.Dispose(); $in.Dispose() }
    } else { Copy-Item $BackupFile $sqlFile -Force }

    if (-not ((Get-Content $sqlFile -Tail 3) -match "Dump completed")) { throw "Backup is incomplete; refusing to restore." }

    Set-Content -Path $optionFile -Encoding ascii -Value "[client]`nuser=$user`npassword=`"$password`"`nhost=$DbHost`nport=$Port"
    Get-Content $sqlFile -Raw -Encoding utf8 | & $mysql "--defaults-extra-file=$optionFile" --default-character-set=utf8mb4 $Database
    if ($LASTEXITCODE -ne 0) { throw "mysql restore failed with exit code $LASTEXITCODE." }
}
finally {
    Remove-Item -Force $sqlFile, $optionFile -ErrorAction SilentlyContinue
}
Write-Output "Restored $Database from $BackupFile. Next: run scripts\verify_database.py."
