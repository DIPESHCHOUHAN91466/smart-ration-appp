<#
.SYNOPSIS
  Set up Android upload keystore and android/key.properties for Smart Ration mobile release.

.DESCRIPTION
  Finds keytool.exe, creates D:\keys\smart-ration-upload.jks (if missing),
  and writes smart_ration_mobile\android\key.properties.
#>
param(
    [string]$KeystorePath = "D:\keys\smart-ration-upload.jks",
    [string]$Alias = "upload"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Smart Ration — Android Release Signing Setup              " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Locate keytool
$keytoolCandidates = @(
    "D:\dev\jdk-21\bin\keytool.exe",
    "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe",
    "C:\Program Files\Java\jdk-21\bin\keytool.exe",
    "C:\Program Files\Java\jdk-17\bin\keytool.exe"
)

$keytool = $null
foreach ($cand in $keytoolCandidates) {
    if (Test-Path $cand) {
        $keytool = $cand
        break
    }
}

if (-not $keytool) {
    $cmd = Get-Command "keytool" -ErrorAction SilentlyContinue
    if ($cmd) { $keytool = $cmd.Source }
}

if (-not $keytool) {
    throw "keytool.exe could not be found. Please ensure JDK 17+ or Android Studio is installed."
}

Write-Host "Using keytool: $keytool" -ForegroundColor Green

# 2. Ensure Keystore Directory
$keyDir = Split-Path -Parent $KeystorePath
if (-not (Test-Path $keyDir)) {
    New-Item -ItemType Directory -Path $keyDir -Force | Out-Null
    Write-Host "Created keystore folder: $keyDir" -ForegroundColor Yellow
}

# 3. Prompt for password
$securePass = Read-Host "Enter a strong password for your release keystore" -AsSecureString
$password = [System.Net.NetworkCredential]::new("", $securePass).Password

if ([string]::IsNullOrWhiteSpace($password)) {
    throw "Password cannot be empty."
}

# 4. Generate Keystore if it doesn't already exist
if (-not (Test-Path $KeystorePath)) {
    Write-Host "Generating keystore at: $KeystorePath..." -ForegroundColor Cyan
    & $keytool -genkeypair -v `
        -keystore $KeystorePath `
        -storetype PKCS12 `
        -keyalg RSA `
        -keysize 2048 `
        -validity 10000 `
        -alias $Alias `
        -storepass $password `
        -keypass $password `
        -dname "CN=Smart Ration, OU=Mobile, O=HSD2C, L=Delhi, ST=Delhi, C=IN"
    
    if ($LASTEXITCODE -ne 0) {
        throw "keytool failed to generate keystore."
    }
    Write-Host "Keystore created successfully!" -ForegroundColor Green
} else {
    Write-Host "Existing keystore found at: $KeystorePath" -ForegroundColor Yellow
}

# 5. Write key.properties
$propsFile = Join-Path $PSScriptRoot "..\android\key.properties"
$forwardSlashKeystore = $KeystorePath -replace "\\", "/"

$propsContent = @"
storeFile=$forwardSlashKeystore
storePassword=$password
keyAlias=$Alias
keyPassword=$password
"@

Set-Content -Path $propsFile -Value $propsContent -Encoding Ascii
Write-Host "Created android/key.properties configured with your release key!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Back up $KeystorePath securely (cloud drive / password manager)." -ForegroundColor Red
Write-Host "Without this key, you will not be able to push updates to the Google Play Store." -ForegroundColor Red
