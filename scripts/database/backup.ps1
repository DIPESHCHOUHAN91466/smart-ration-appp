<#
.SYNOPSIS
  Consistent, compressed, timestamped backup of the Smart Ration MySQL database.

.DESCRIPTION
  Uses mysqldump --single-transaction (consistent InnoDB snapshot, no table locks),
  including schema, data, routines, triggers and events. Output:
    database\backups\<database>_<yyyyMMdd_HHmmss>.sql.gz
  An existing file is never overwritten. The password is read from the environment
  and written only to a temporary MySQL option file (deleted afterwards), so it never
  appears on the command line or in the process list.

.EXAMPLE
  $env:SMARTRATION_DB_USER = "smartration_app"
  $env:SMARTRATION_DB_PASSWORD = "<password>"
  .\scripts\database\backup.ps1
#>
[CmdletBinding()]
param(
    [string]$Database = "smartration",
    [string]$DbHost = "localhost",
    [int]$Port = 3306,
    [string]$OutputDir = "",
    [string]$MySqlBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin"
)
$ErrorActionPreference = "Stop"
# ($PSScriptRoot is empty in param defaults on Windows PowerShell 5.1)
if (-not $OutputDir) { $OutputDir = Join-Path $PSScriptRoot "..\..\database\backups" }

$user = $env:SMARTRATION_DB_USER
$password = $env:SMARTRATION_DB_PASSWORD
if (-not $user -or -not $password) {
    throw "Set SMARTRATION_DB_USER and SMARTRATION_DB_PASSWORD in the environment first."
}
$mysqldump = Join-Path $MySqlBin "mysqldump.exe"
if (-not (Test-Path $mysqldump)) { throw "mysqldump not found at $mysqldump (use -MySqlBin)." }

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sqlFile = Join-Path $OutputDir "${Database}_$stamp.sql"
$gzFile = "$sqlFile.gz"
if ((Test-Path $sqlFile) -or (Test-Path $gzFile)) { throw "Backup $gzFile already exists; refusing to overwrite." }

$optionFile = [System.IO.Path]::GetTempFileName()
try {
    Set-Content -Path $optionFile -Encoding ascii -Value "[client]`nuser=$user`npassword=`"$password`"`nhost=$DbHost`nport=$Port"
    # --no-tablespaces: the application account deliberately lacks the global PROCESS privilege.
    & $mysqldump "--defaults-extra-file=$optionFile" --single-transaction --quick --routines --triggers --events `
        --hex-blob --no-tablespaces --set-gtid-purged=OFF --default-character-set=utf8mb4 `
        "--result-file=$sqlFile" $Database
    if ($LASTEXITCODE -ne 0) { throw "mysqldump failed with exit code $LASTEXITCODE." }
}
finally {
    Remove-Item -Force $optionFile -ErrorAction SilentlyContinue
}

# Integrity check before compressing: a complete dump ends with this marker.
$tail = Get-Content $sqlFile -Tail 3
if (-not ($tail -match "Dump completed")) { throw "Dump looks incomplete (no 'Dump completed' marker): $sqlFile" }

$in = [System.IO.File]::OpenRead($sqlFile)
$out = [System.IO.File]::Create($gzFile)
$gz = New-Object System.IO.Compression.GZipStream($out, [System.IO.Compression.CompressionLevel]::Optimal)
try { $in.CopyTo($gz) } finally { $gz.Dispose(); $out.Dispose(); $in.Dispose() }
Remove-Item $sqlFile

$sha = (Get-FileHash $gzFile -Algorithm SHA256).Hash
Set-Content -Path "$gzFile.sha256" -Encoding ascii -Value "$sha  $(Split-Path $gzFile -Leaf)"
$size = [math]::Round((Get-Item $gzFile).Length / 1MB, 2)
Write-Output "Backup written: $gzFile ($size MB), SHA-256 $sha"
