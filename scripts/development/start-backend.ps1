# Starts the C# API (http://localhost:5188). For the whole stack use scripts\development\start-all.ps1.
Write-Host "Starting Smart Ration C# API..." -ForegroundColor Cyan
Set-Location (Join-Path $PSScriptRoot "..\..\backend\SmartRation.Api")
dotnet run --launch-profile http
