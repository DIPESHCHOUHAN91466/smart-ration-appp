<#
.SYNOPSIS
  Check every dependency for known vulnerabilities. Read-only; needs internet access.

.DESCRIPTION
  Python API + AI service   pip-audit on their requirements files
  Frontend                  npm audit, production dependencies, fails on high or critical
  C# API + tests            dotnet list package --vulnerable --include-transitive (any finding fails)
  Exit code 0 = no vulnerabilities found (at the thresholds above), 1 otherwise. CI runs the same checks.

.EXAMPLE
  .\scripts\development\audit-dependencies.ps1      (or: .\sr.ps1 audit)
#>
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pyExe = Join-Path $root "backend\SmartRation.Python\.venv\Scripts\python.exe"
$failed = 0

function Result([string]$Name, [bool]$Ok, [string]$Detail) {
    Write-Host ("{0,-9} {1,-34} {2}" -f $(if ($Ok) { "[PASS]" } else { "[FAIL]" }), $Name, $Detail) -ForegroundColor $(if ($Ok) { "Green" } else { "Red" })
    if (-not $Ok) { $script:failed++ }
}

foreach ($req in @("backend\SmartRation.Python\requirements-dev.txt", "backend\SmartRation.AI\requirements.txt")) {
    # stdout = the findings table (empty when clean); stderr = progress and summary notes only.
    $out = & $pyExe -m pip_audit -r (Join-Path $root $req) --progress-spinner off 2>$null | Out-String
    $ok = ($LASTEXITCODE -eq 0)
    Result "Python: $req" $ok $(if ($ok) { "no known vulnerabilities" } else { "`n$($out.Trim())" })
}

Push-Location (Join-Path $root "frontend")
$out = npm audit --omit=dev --audit-level=high 2>&1 | Out-String
$code = $LASTEXITCODE
Pop-Location
Result "npm (production dependencies)" ($code -eq 0) ($out.Trim().Split("`n")[-1].Trim())

$out = dotnet list (Join-Path $root "SmartRation.sln") package --vulnerable --include-transitive 2>&1 | Out-String
$vulnerable = $out -match "has the following vulnerable packages"
Result "C# (SmartRation.sln, transitive)" (-not $vulnerable -and $LASTEXITCODE -eq 0) $(if ($vulnerable) { "vulnerable packages found - run: dotnet list SmartRation.sln package --vulnerable --include-transitive" } else { "no vulnerable packages" })

Write-Host ""
if ($failed) { Write-Host "$failed dependency check(s) failed." -ForegroundColor Red; exit 1 }
Write-Host "No known vulnerabilities." -ForegroundColor Green
exit 0
