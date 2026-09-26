<#
.SYNOPSIS
  First-time (or refresh) setup of the development environment. Safe to run again at any time.

.DESCRIPTION
  1. Checks the required tools: Python 3.12+, .NET 8 SDK, Node.js 18+ and npm (stops if one is missing).
  2. Python API and AI service: creates each .venv if missing (or rebuilds it if it was created in another
     folder, i.e. the project was moved), then installs its requirements.
  3. Frontend: npm install.
  4. C#: dotnet restore SmartRation.sln.
  5. .env files: copies each .env.example to .env ONLY when .env does not exist (never overwrites).
     The copies contain placeholders: fill in the database password and secrets yourself.
  It does not create or change any database. Afterwards: seed-demo-data.ps1 (database), then start-all.ps1.
  Works from any current directory. -CheckOnly reports what would be done without changing anything.

.EXAMPLE
  .\scripts\development\setup.ps1
  .\scripts\development\setup.ps1 -CheckOnly
#>
param([switch]$CheckOnly)
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "_common.ps1")
$script:failed = 0

function Step([string]$Name) { Write-Host "`n== $Name" -ForegroundColor Cyan }
function Fail([string]$Message) { Write-Host "[ERROR]   $Message" -ForegroundColor Red; $script:failed++ }
function Info([string]$Message) { Write-Host "[OK]      $Message" -ForegroundColor Green }
function Todo([string]$Message) { Write-Host "[TODO]    $Message" -ForegroundColor Yellow }

function Invoke-Checked([string]$Description, [string]$Directory, [scriptblock]$Command) {
    if ($CheckOnly) { Todo "would run: $Description"; return }
    Write-Host "  $Description" -ForegroundColor DarkGray
    Push-Location $Directory
    try { & $Command; $code = $LASTEXITCODE } finally { Pop-Location }
    if ($code -ne 0) { Fail "$Description failed (exit code $code) in $Directory" } else { Info $Description }
}

# ------------------------------------------------------------------ 1. tools
Step "Tools"
$tools = @(
    @{ Name = "Python 3.12+"; Command = "python"; Args = @("--version"); Pattern = "Python 3\.(1[2-9]|[2-9]\d)"; Url = "https://www.python.org/downloads/ (tick 'Add python.exe to PATH')" },
    @{ Name = ".NET SDK 8+"; Command = "dotnet"; Args = @("--version"); Pattern = "^(8|9|1\d)\."; Url = "https://dotnet.microsoft.com/download/dotnet/8.0" },
    @{ Name = "Node.js 18+"; Command = "node"; Args = @("--version"); Pattern = "^v(1[89]|[2-9]\d)\."; Url = "https://nodejs.org (LTS)" },
    @{ Name = "npm"; Command = "npm"; Args = @("--version"); Pattern = "^\d+\."; Url = "comes with Node.js" }
)
foreach ($t in $tools) {
    $version = $null
    if (Get-Command $t.Command -ErrorAction SilentlyContinue) { $version = ((& $t.Command @($t.Args) 2>&1) | Select-Object -First 1).ToString().Trim() }
    if (-not $version) { Fail "$($t.Name) MISSING - install: $($t.Url)" }
    elseif ($version -notmatch $t.Pattern) { Fail "$($t.Name) WRONG VERSION ($version) - install: $($t.Url)" }
    else { Info "$($t.Name): $version" }
}
if ($script:failed) {
    Write-Host "`nInstall the missing tools, open a new terminal, and run this script again." -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------ 2. Python virtualenvs
foreach ($svc in @(
        @{ Name = "Python API"; Dir = "backend\SmartRation.Python"; Requirements = "requirements-dev.txt" },
        @{ Name = "AI service"; Dir = "backend\SmartRation.AI"; Requirements = "requirements.txt" })) {
    Step $svc.Name
    $dir = Join-Path $root $svc.Dir
    $venvPython = Join-Path $dir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) { Invoke-Checked "python -m venv .venv" $dir { python -m venv .venv } }
    elseif (Test-VenvMoved (Join-Path $dir ".venv")) {
        # Created in another folder (project moved/copied): its .exe launchers point there. Rebuild in place.
        Todo ".venv was created in $(Get-VenvOrigin (Join-Path $dir '.venv')) - rebuilding it here"
        Invoke-Checked "python -m venv --clear .venv" $dir { python -m venv --clear .venv }
    }
    else { Info ".venv exists" }
    Invoke-Checked "pip install -r $($svc.Requirements)" $dir { & .venv\Scripts\python -m pip install --disable-pip-version-check -q -r $svc.Requirements }
}

# ------------------------------------------------------------------ 3. frontend
Step "Frontend"
Invoke-Checked "npm install" (Join-Path $root "frontend") { npm install --no-fund --no-audit }

# ------------------------------------------------------------------ 4. C#
Step "C# API"
Invoke-Checked "dotnet restore SmartRation.sln" $root { dotnet restore SmartRation.sln --nologo -v q }

# ------------------------------------------------------------------ 5. .env files (never overwritten)
Step ".env files"
foreach ($dir in @(".", "backend\SmartRation.Python", "backend\SmartRation.AI", "frontend")) {
    $example = Join-Path $root "$dir\.env.example"
    $target = Join-Path $root "$dir\.env"
    $shown = if ($dir -eq ".") { ".env" } else { "$dir\.env" }
    if (-not (Test-Path $example)) { continue }
    if (Test-Path $target) { Info "$shown exists (left unchanged)"; continue }
    if ($CheckOnly) { Todo "would create $shown from .env.example"; continue }
    Copy-Item $example $target
    Todo "created $shown from .env.example - fill in the database password and secrets before starting"
}
Write-Host "  The C# API reads its secrets from dotnet user-secrets, not a file: see docs\development\LOCAL_SETUP.md." -ForegroundColor DarkGray

Write-Host ""
if ($script:failed) {
    Write-Host "$($script:failed) step(s) failed - read the messages above." -ForegroundColor Red
    exit 1
}
Write-Host "Setup complete. Next:" -ForegroundColor Green
Write-Host "  .\scripts\development\seed-demo-data.ps1   (first time: database schema + synthetic demo data)"
Write-Host "  .\scripts\development\start-all.ps1        (start everything)"
Write-Host "  .\scripts\development\health-check.ps1     (check everything)"
exit 0
