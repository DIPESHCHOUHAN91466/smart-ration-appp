<#
Proves, on THIS PC's MySQL, that the API works with a rows-only account and that such an account cannot change
the schema (tests/integration/mysql_suite/test_09_least_privilege.py; CI runs the same tests).

  powershell -ExecutionPolicy Bypass -File scripts\database\run-least-privilege-tests.ps1

Asks for the local MySQL root password (not shown, not saved). The tests create and then drop a throwaway account
'sr_rows_only_test' and use only the separate test database smartration_test.
#>
param([string]$RootUser = "root", [string]$MySqlHost = "127.0.0.1", [int]$Port = 3306)
$ErrorActionPreference = "Stop"
$backend = Resolve-Path (Join-Path $PSScriptRoot "..\..\backend\SmartRation")
$python = Join-Path $backend ".venv\Scripts\python.exe"

$secure = Read-Host "Local MySQL password for '$RootUser'" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
$enc = [Uri]::EscapeDataString($plain)

# The test database URL is the app's own .env account, pointed at smartration_test (as the CI and the full suite do).
$env:TEST_MYSQL_ROOT_URL = "mysql+pymysql://${RootUser}:$enc@${MySqlHost}:$Port/?charset=utf8mb4"
$env:TEST_DATABASE_URL = & $python -c @"
from pathlib import Path
from sqlalchemy.engine import make_url
env = dict(l.split('=', 1) for l in Path(r'$backend\.env').read_text(encoding='utf-8').splitlines() if '=' in l and not l.lstrip().startswith('#'))
print(make_url(env['DATABASE_URL'].strip()).set(database='smartration_test').render_as_string(hide_password=False))
"@
try {
    Push-Location $backend
    & $python -m pytest tests/integration/mysql_suite/test_09_least_privilege.py -p no:cacheprovider -q -W ignore
    $code = $LASTEXITCODE
} finally {
    Pop-Location
    Remove-Item Env:TEST_MYSQL_ROOT_URL, Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
    $plain = $null; $enc = $null
}
if ($code -eq 0) { Write-Host "PASSED: the API works with a rows-only account, and that account cannot change tables." }
else { Write-Host "FAILED (exit $code): send the output above (it contains no password)." }
exit $code
