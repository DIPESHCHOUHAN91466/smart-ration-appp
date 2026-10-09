<#
Turn on e-mail delivery of one-time codes (password reset, sign-in, counter check) on the Azure app, with Gmail.

  powershell -ExecutionPolicy Bypass -File scripts\azure\set-email.ps1

Before: in your Google account turn on 2-Step Verification, then create an App password
(myaccount.google.com/apppasswords, name it "Smart Ration"): 16 letters. Type it when asked; it is not shown,
not saved on this PC, and goes straight into the app's settings on Azure. The app restarts by itself (about a minute).
To turn e-mail off again: run with -Off.
#>
param(
    [string]$ResourceGroup = "SmartRation-AI",
    [string]$AppName = "smartration-api-prod",
    [switch]$Off
)
$ErrorActionPreference = "Stop"
$az = (Get-Command az -ErrorAction SilentlyContinue).Source
if (-not $az) { $az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" }

if ($Off) {
    & $az webapp config appsettings delete -g $ResourceGroup -n $AppName --setting-names SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_PASSWORD SMTP_FROM --output none
    if ($LASTEXITCODE -ne 0) { throw "az failed" }
    Write-Host "E-mail delivery turned off."
    return
}

$gmail = (Read-Host "Gmail address that sends the codes").Trim()
if ($gmail -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "That is not an e-mail address." }
$secure = Read-Host "Gmail app password (16 letters, spaces allowed)" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
$plain = ($plain -replace '\s', '')
if ($plain.Length -ne 16) { throw "A Gmail app password has 16 letters; this one has $($plain.Length)." }

# Through a temporary file: the password never appears on a command line.
$tmp = Join-Path $env:TEMP ("sr-smtp-" + [guid]::NewGuid() + ".json")
try {
    @{ SMTP_HOST = "smtp.gmail.com"; SMTP_PORT = "587"; SMTP_USERNAME = $gmail; SMTP_PASSWORD = $plain; SMTP_FROM = $gmail } |
        ConvertTo-Json | Set-Content -Encoding utf8 $tmp
    & $az webapp config appsettings set -g $ResourceGroup -n $AppName --settings "@$tmp" --output none
    if ($LASTEXITCODE -ne 0) { throw "az failed" }
} finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
    $plain = $null
}
Write-Host "Done. In about a minute, try 'Forgot password' on the website: the code arrives at the account's e-mail."
