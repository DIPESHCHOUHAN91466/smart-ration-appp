<#
Deploy Smart Ration (website + API in one app) to an existing Azure App Service (Linux, Python) and MySQL Flexible Server.

  powershell -ExecutionPolicy Bypass -File scripts\azure\deploy.ps1
  powershell -ExecutionPolicy Bypass -File scripts\azure\deploy.ps1 -SkipSettings   # code only, settings untouched

Before: `az login`, and `python scripts\azure\build_package.py` (makes build\azure\smartration-app.zip).
Staging (a separate app and database; never production's):
  powershell -ExecutionPolicy Bypass -File scripts\azure\deploy.ps1 -AppName smartration-api-staging

Secrets are never printed:
  * DATABASE_URL is read from a local, git-ignored file (-DatabaseUrlFile, line DATABASE_URL=...). Each app has its
    own default file (production: .env.azure-local-copy, staging: .env.azure-staging); any other app must name one.
    An optional line MIGRATION_DATABASE_URL=... gives the account that changes tables, so DATABASE_URL can be a
    rows-only account; staging REQUIRES both, with different accounts.
  * Fail closed: the app name decides ENVIRONMENT (smartration-api-prod = production, anything else = staging), and
    every URL must point at that app's own database (smartration / smartration_staging), or nothing is changed.
  * JWT_SECRET_KEY, QR_SECRET, MFA_ENCRYPTION_KEY, SEED_DEMO_PASSWORD are generated ONCE, only when the app does
    not have them yet. They are never replaced afterwards: a new QR_SECRET would invalidate every issued QR code.
  * The demo-account password is written to build\azure\demo-accounts.txt (git-ignored) for you, nowhere else.
#>
param(
    [string]$ResourceGroup = "SmartRation-AI",
    [string]$AppName = "smartration-api-prod",
    [string]$DatabaseUrlFile = "",
    [string]$Package = "build\azure\smartration-app.zip",
    [switch]$SkipSettings
)
$isProduction = $AppName -eq "smartration-api-prod"
$environmentName = if ($isProduction) { "production" } else { "staging" }
$expectedDatabase = if ($isProduction) { "smartration" } else { "smartration_staging" }
if (-not $DatabaseUrlFile) {
    $DatabaseUrlFile = if ($isProduction) { "backend\SmartRation\.env.azure-local-copy" }
                       elseif ($AppName -eq "smartration-api-staging") { "backend\SmartRation\.env.azure-staging" }
                       else { throw "Give -DatabaseUrlFile for $AppName (there is no default, so production's can never be used by mistake)." }
}
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" }
function Az { & $az @args; if ($LASTEXITCODE -ne 0) { throw "az $($args[0..2] -join ' ') failed ($LASTEXITCODE)" } }
function NewSecret([int]$bytes = 48) {
    $b = New-Object byte[] $bytes
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    ([Convert]::ToBase64String($b)).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

if (-not (Test-Path $Package)) { throw "$Package not found: run python scripts\azure\build_package.py first." }
$hostName = Az webapp show -g $ResourceGroup -n $AppName --query defaultHostName -o tsv
$site = "https://$hostName"
Write-Host "Target: $site"

if (-not $SkipSettings) {
    Write-Host "1/4 Runtime, start command, HTTPS only"
    # Through a JSON file: az is a .cmd script, and cmd.exe would read the "|" in "PYTHON|3.13" as a pipe.
    $siteFile = Join-Path $env:TEMP ("sr-site-" + [guid]::NewGuid() + ".json")
    try {
        @{ linuxFxVersion = "PYTHON|3.13"; appCommandLine = "sh startup.sh"; alwaysOn = $true
           ftpsState = "Disabled"; minTlsVersion = "1.2" } | ConvertTo-Json | Set-Content -Encoding utf8 $siteFile
        Az webapp config set -g $ResourceGroup -n $AppName --generic-configurations "@$siteFile" --output none
    } finally { Remove-Item $siteFile -ErrorAction SilentlyContinue }
    Az webapp update -g $ResourceGroup -n $AppName --https-only true --output none

    Write-Host "2/4 Application settings (values not shown)"
    $existing = @(Az webapp config appsettings list -g $ResourceGroup -n $AppName --query "[].name" -o tsv)
    if (-not (Test-Path $DatabaseUrlFile)) { throw "$DatabaseUrlFile not found." }
    function ReadUrl([string]$name, [bool]$required) {
        $l = Select-String -Path $DatabaseUrlFile -Pattern "^$name=(.+)$" | Select-Object -First 1
        if (-not $l) { if ($required) { throw "No $name= line in $DatabaseUrlFile" } else { return "" } }
        $u = $l.Matches[0].Groups[1].Value.Trim().Trim('"')
        # Azure MySQL requires TLS; its CA (DigiCert Global Root G2) is in the system CA bundle of the App Service image.
        if ($u -notmatch 'ssl_ca=|ssl=') { $u += $(if ($u.Contains("?")) { "&" } else { "?" }) + "ssl_ca=/etc/ssl/certs/ca-certificates.crt" }
        return $u
    }
    function UrlParts([string]$u) {   # account and database name only; the password is never read out or printed
        if ($u -notmatch '^mysql\+pymysql://([^:@/]+)(:[^@]*)?@[^/]+/([^?]+)') { throw "A URL in $DatabaseUrlFile is not a mysql+pymysql:// URL." }
        return @{ User = $Matches[1]; Database = $Matches[3] }
    }
    $dbUrl = ReadUrl "DATABASE_URL" $true
    $migrationUrl = ReadUrl "MIGRATION_DATABASE_URL" (-not $isProduction)
    foreach ($u in @($dbUrl, $migrationUrl) | Where-Object { $_ }) {
        $db = (UrlParts $u).Database
        if ($db -ne $expectedDatabase) { throw "Refusing: $DatabaseUrlFile points at database '$db'; $AppName must use '$expectedDatabase'. Nothing was changed." }
    }
    if ($migrationUrl -and (UrlParts $dbUrl).User -eq (UrlParts $migrationUrl).User) {
        throw "Refusing: DATABASE_URL (day-to-day, rows only) and MIGRATION_DATABASE_URL (changes tables) must be different accounts."
    }
    Write-Host "   $environmentName app, database '$expectedDatabase', runtime and migration accounts checked"

    $settings = [ordered]@{
        ENVIRONMENT = $environmentName; DATA_MODE = "synthetic"; DATABASE_URL = $dbUrl
        CORS_ORIGINS = $site
        TRUSTED_PROXY_HOPS = "1"                       # App Service's front end appends the client address
        DEMO_OTP_ENABLED = "false"
        SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT = "true"    # synthetic demo: sign-in codes are NOT delivered by SMS
        LEGACY_API_URL = ""; AI_SERVICE_URL = ""
        RUN_DB_SETUP = "true"; RUN_DB_SEED = "true"    # non-destructive: creates/updates the schema, seeds EMPTY tables only
        SCM_DO_BUILD_DURING_DEPLOYMENT = "true"        # App Service installs requirements.txt
        WEBSITES_CONTAINER_START_TIME_LIMIT = "900"    # the first start creates the schema
    }
    if ($migrationUrl) { $settings["MIGRATION_DATABASE_URL"] = $migrationUrl }   # only start-up migrations use it
    # One file per app: deploying another app (e.g. staging) must never overwrite production's demo-account record.
    $demoFile = if ($AppName -eq "smartration-api-prod") { "build\azure\demo-accounts.txt" } else { "build\azure\demo-accounts.$AppName.txt" }
    foreach ($name in "JWT_SECRET_KEY", "QR_SECRET", "MFA_ENCRYPTION_KEY", "SEED_DEMO_PASSWORD") {
        if ($existing -notcontains $name) {
            $value = if ($name -eq "SEED_DEMO_PASSWORD") { "Demo-" + (NewSecret 9) } else { NewSecret }
            $settings[$name] = $value
            if ($name -eq "SEED_DEMO_PASSWORD") {
                Set-Content -Encoding utf8 $demoFile @(
                    "Demo accounts on $site (synthetic data). Keep this file private.",
                    "rural@example.com / shop@example.com / officer@example.com",
                    "password: $value")
                Write-Host "   demo-account password saved to $demoFile"
            }
        }
    }
    # Settings go through a temporary JSON file: secrets stay off the command line, and '&' in the URL is safe.
    $tmp = Join-Path $env:TEMP ("sr-settings-" + [guid]::NewGuid() + ".json")
    try {
        $settings | ConvertTo-Json | Set-Content -Encoding utf8 $tmp
        Az webapp config appsettings set -g $ResourceGroup -n $AppName --settings "@$tmp" --output none
    } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
    if ($existing -contains "PYTHONPATH") {   # an old manual setting; App Service sets the paths itself
        Az webapp config appsettings delete -g $ResourceGroup -n $AppName --setting-names PYTHONPATH --output none
    }
}

Write-Host "3/4 Uploading $Package (App Service installs the dependencies; takes a few minutes)"
Az webapp deploy -g $ResourceGroup -n $AppName --src-path $Package --type zip --track-status false --timeout 900000 --output none

Write-Host "4/4 Waiting for $site/health/live"
$deadline = (Get-Date).AddMinutes(15)
while ($true) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 30 "$site/health/live"
        if ($r.StatusCode -eq 200) { break }
    } catch { }
    if ((Get-Date) -gt $deadline) { throw "Not healthy after 15 minutes: check Log stream in the Azure portal." }
    Start-Sleep -Seconds 15
}
(Invoke-WebRequest -UseBasicParsing -TimeoutSec 60 "$site/health").Content
Write-Host "Deployed: $site"
