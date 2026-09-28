<#
.SYNOPSIS
  Smoke-tests a running deployment (local stack or public URL) with tests/smoke. Read-only, no sign-in.

.EXAMPLE
  .\scripts\deployment\verify-deployment.ps1                                   # the local stack on :8000
  .\scripts\deployment\verify-deployment.ps1 https://smart-ration-hsd2c.onrender.com
#>
param([Parameter(Position = 0)][string]$BaseUrl = "http://127.0.0.1:8000")
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$python = Join-Path $root "backend\SmartRation\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python virtualenv missing: run .\sr.ps1 setup first." }

Push-Location $root
try {
    & $python -m pytest tests/smoke -p no:warnings -rs --base-url $BaseUrl
    $code = $LASTEXITCODE
}
finally { Pop-Location }
if ($code -eq 0) { Write-Host "Deployment at $BaseUrl passed the smoke test." -ForegroundColor Green }
else { Write-Host "Smoke test FAILED for $BaseUrl (exit $code)." -ForegroundColor Red }
exit $code
