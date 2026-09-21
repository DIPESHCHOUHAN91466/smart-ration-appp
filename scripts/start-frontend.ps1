Write-Host "Starting Smart Ration Frontend..." -ForegroundColor Cyan

Set-Location "\..\frontend"

if (!(Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

npm run dev
