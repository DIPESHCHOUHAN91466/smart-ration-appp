<#
Switches the live app to the rows-only database account created with scripts\database\azure-runtime-account.sql.

  powershell -ExecutionPolicy Bypass -File scripts\azure\set-runtime-db-account.ps1          # switch
  powershell -ExecutionPolicy Bypass -File scripts\azure\set-runtime-db-account.ps1 -Undo    # switch back

What it does (no value is ever printed):
  1. Keeps today's DATABASE_URL (the account that may change tables) as MIGRATION_DATABASE_URL: only the start-up
     migration step uses it.
  2. Sets DATABASE_URL to the same server and database with the rows-only account and the password you type.
  3. Waits for /health/db. If the app is not healthy within 5 minutes it switches back by itself.
#>
param(
    [string]$ResourceGroup = "SmartRation-AI",
    [string]$AppName = "smartration-api-prod",
    [string]$RuntimeUser = "smartration_runtime",
    [switch]$Undo
)
$ErrorActionPreference = "Stop"
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" }
$site = "https://" + (& $az webapp show -g $ResourceGroup -n $AppName --query defaultHostName -o tsv)

function Get-Setting([string]$name) {
    $v = & $az webapp config appsettings list -g $ResourceGroup -n $AppName --query "[?name=='$name'].value | [0]" -o tsv
    if ($LASTEXITCODE -ne 0) { throw "az failed" }
    return ($v | Out-String).Trim()
}
function Set-Settings([hashtable]$values) {
    $tmp = Join-Path $env:TEMP ("sr-db-" + [guid]::NewGuid() + ".json")
    try {
        $values | ConvertTo-Json | Set-Content -Encoding utf8 $tmp
        & $az webapp config appsettings set -g $ResourceGroup -n $AppName --settings "@$tmp" --output none
        if ($LASTEXITCODE -ne 0) { throw "az failed" }
    } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
}
function Wait-Healthy([int]$minutes) {
    $deadline = (Get-Date).AddMinutes($minutes)
    Start-Sleep -Seconds 20
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-RestMethod -TimeoutSec 30 "$site/health/db"
            if ($r.status -eq "healthy") { return $r }
        } catch { }
        Start-Sleep -Seconds 15
    }
    return $null
}

$migration = Get-Setting "MIGRATION_DATABASE_URL"
if ($Undo) {
    if (-not $migration) { throw "MIGRATION_DATABASE_URL is not set: nothing to undo." }
    Set-Settings @{ DATABASE_URL = $migration }
    & $az webapp config appsettings delete -g $ResourceGroup -n $AppName --setting-names MIGRATION_DATABASE_URL --output none
    $h = Wait-Healthy 5
    if ($h) { Write-Host "Switched back to the original account; database $($h.status)." } else { Write-Host "Switched back, but /health/db is not healthy yet: check the Log stream." }
    return
}

$current = Get-Setting "DATABASE_URL"
$uri = [Uri]$current
$currentUser = [Uri]::UnescapeDataString($uri.UserInfo.Split(":")[0])
if ($currentUser -eq $RuntimeUser) { Write-Host "The app already uses '$RuntimeUser'. Nothing to do."; return }

$secure = Read-Host "Password of MySQL account '$RuntimeUser' (as set in azure-runtime-account.sql)" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
$runtimeUrl = $current.Replace($uri.UserInfo + "@", ("{0}:{1}@" -f $RuntimeUser, [Uri]::EscapeDataString($plain)))
$plain = $null

$values = @{ DATABASE_URL = $runtimeUrl }
if (-not $migration) { $values.MIGRATION_DATABASE_URL = $current }   # the account that may change tables
Set-Settings $values
Write-Host "Settings changed; the app restarts (about a minute). Checking health..."
$h = Wait-Healthy 5
if ($h) {
    Write-Host "OK: the app now uses '$RuntimeUser' (rows only). Database $($h.status), migrations $($h.migrations), encryption $($h.encryption)."
} else {
    Write-Host "Not healthy after 5 minutes: switching back to the original account."
    Set-Settings @{ DATABASE_URL = $current }
    $h = Wait-Healthy 5
    Write-Host ("Switched back; database " + $(if ($h) { $h.status } else { "still not healthy: check the Log stream" }))
    exit 1
}
