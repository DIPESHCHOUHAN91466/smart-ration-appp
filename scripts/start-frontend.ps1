# Starts the frontend dev server (http://localhost:5173). For the whole stack use scripts\development\start-all.ps1.
Write-Host "Starting Smart Ration Frontend..." -ForegroundColor Cyan
Set-Location (Join-Path $PSScriptRoot "..\frontend")

if (!(Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

npm run dev
