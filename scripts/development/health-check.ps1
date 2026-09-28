<#
.SYNOPSIS
  Check the tools, the project setup and every running Smart Ration component. Read-only.

.DESCRIPTION
  Prints one line per check:
    [PASS]            works
    [FAIL]            broken: must be fixed
    [WARNING]         optional part down, or degraded
    [NOT CONFIGURED]  never set up (missing tool, virtualenv, packages or .env); for a REQUIRED part
                      this also makes the exit code 1 - run scripts\development\setup.ps1
  Sections:
    Tools     Python, .NET 8 SDK, Node.js, npm, Git, MySQL server (+ optional mysql client, Docker)
    Project   solution, Python virtualenvs, imports, pytest, frontend packages, .env files (-Deep: C# + frontend builds)
    Services  frontend :5173, Python API :8000 (/health, /ready, /health/db, chatbot), C# API :5188, AI :8001, port clashes
    Database  schema, migration version and reference data (backend\SmartRation\scripts\verify_database.py)
  Works from any current directory. Exit code 0 = no FAIL and nothing required NOT CONFIGURED.
  -SkipServices checks only tools, project and database. -Deep also builds C# and the frontend (slower).

.EXAMPLE
  .\scripts\development\health-check.ps1
  .\scripts\development\health-check.ps1 -SkipServices
  .\scripts\development\health-check.ps1 -Deep
#>
param([switch]$SkipServices, [switch]$Deep)
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "_common.ps1")
$script:counts = @{ PASS = 0; FAIL = 0; WARNING = 0; "NOT CONFIGURED" = 0 }
$script:blocking = 0   # FAIL, or a required part NOT CONFIGURED

function Report([string]$Level, [string]$Name, [string]$Detail, [switch]$Optional) {
    $color = @{ PASS = "Green"; WARNING = "Yellow"; FAIL = "Red"; "NOT CONFIGURED" = "Magenta" }[$Level]
    Write-Host ("{0,-17} {1,-26} {2}" -f "[$Level]", $Name, $Detail) -ForegroundColor $color
    $script:counts[$Level]++
    if ($Level -eq "FAIL" -or ($Level -eq "NOT CONFIGURED" -and -not $Optional)) { $script:blocking++ }
}

function Check([bool]$Ok, [string]$Name, [string]$Detail, [string]$FailLevel = "FAIL", [switch]$Optional) {
    Report $(if ($Ok) { "PASS" } else { $FailLevel }) $Name $Detail -Optional:$Optional
}

# A required tool: NOT CONFIGURED when absent, FAIL when the version is wrong.
function Tool([string]$Version, [string]$Pattern, [string]$Name, [string]$Install) {
    if (-not $Version) { Report "NOT CONFIGURED" $Name "MISSING - install: $Install" }
    else { Check ($Version -match $Pattern) $Name $(if ($Version -match $Pattern) { $Version } else { "WRONG VERSION ($Version) - install: $Install" }) }
}

function Version([string]$Command, [string[]]$Arguments) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) { return $null }
    try { return ((& $Command @Arguments 2>&1) | Select-Object -First 1).ToString().Trim() } catch { return $null }
}

function Probe([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return @{ Status = [int]$response.StatusCode; Body = $response.Content }
    } catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        return @{ Status = $status; Body = "" }
    }
}

# ------------------------------------------------------------------ tools
Write-Host "Tools" -ForegroundColor Cyan
Tool (Version "python" @("--version")) "Python 3\.(1[2-9]|[2-9]\d)" "Python 3.12+" "https://www.python.org/downloads/"
Tool (Version "dotnet" @("--version")) "^(8|9|1\d)\." ".NET SDK 8+" "https://dotnet.microsoft.com/download/dotnet/8.0"
Tool (Version "node" @("--version")) "^v(1[89]|[2-9]\d)\." "Node.js 18+" "https://nodejs.org (LTS)"
Tool (Version "npm" @("--version")) "^\d+\." "npm" "comes with Node.js"
$git = Version "git" @("--version")
Check ([bool]$git) "Git (optional)" $(if ($git) { $git } else { "not installed - https://git-scm.com" }) "NOT CONFIGURED" -Optional
$mysqlService = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
$mysqlPort = [bool](Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue)
if ($mysqlPort) { Report "PASS" "MySQL server :3306" ("listening" + $(if ($mysqlService) { " (service MySQL80: $($mysqlService.Status))" })) }
elseif ($mysqlService) { Report "FAIL" "MySQL server :3306" "service MySQL80 is $($mysqlService.Status) - Start-Service MySQL80 (as administrator)" }
else { Report "NOT CONFIGURED" "MySQL server :3306" "not installed - MySQL 8 Community Server (docs\development\LOCAL_SETUP.md)" }
$client = Version "mysql" @("--version")
Check ([bool]$client) "mysql client (optional)" $(if ($client) { $client } else { "not on PATH (only backup/restore scripts use it)" }) "NOT CONFIGURED" -Optional
$docker = Version "docker" @("--version")
if (-not $docker) { Report "NOT CONFIGURED" "Docker (optional)" "not installed (only needed for docker-compose)" -Optional }
else {
    & docker info --format "{{.ServerVersion}}" *> $null
    $engine = ($LASTEXITCODE -eq 0)
    Check $engine "Docker (optional)" $(if ($engine) { "$docker, engine running" } else { "$docker, engine NOT running (start Docker Desktop to use docker-compose)" }) "WARNING"
}

# ------------------------------------------------------------------ project
Write-Host "`nProject ($root)" -ForegroundColor Cyan
Check (Test-Path (Join-Path $root "SmartRation.sln")) "Solution file" "SmartRation.sln"
$pyDir = Join-Path $root "backend\SmartRation"
$pyExe = Join-Path $pyDir ".venv\Scripts\python.exe"
Check (Test-Path $pyExe) "Python API virtualenv" $(if (Test-Path $pyExe) { ".venv present" } else { "missing - run scripts\development\setup.ps1" }) "NOT CONFIGURED"
if (Test-Path $pyExe) {
    Push-Location $pyDir
    $imports = & $pyExe -c "import app.main, app.synthetic, app.database.session; print('ok')" 2>&1 | Select-Object -Last 1
    Pop-Location
    Check ("$imports" -eq "ok") "Python API imports" $(if ("$imports" -eq "ok") { "app.main, app.synthetic, app.database.session" } else { "$imports" })
    $pytest = & $pyExe -m pytest --version 2>&1 | Select-Object -First 1
    Check ("$pytest" -match "^pytest \d") "pytest" $(if ("$pytest" -match "^pytest \d") { "$pytest" } else { "missing - pip install -r requirements-dev.txt" }) "NOT CONFIGURED"
}
$aiExe = Join-Path $root "ai\.venv\Scripts\python.exe"
foreach ($venv in @((Join-Path $pyDir ".venv"), (Join-Path $root "ai\.venv"))) {
    if ((Test-Path $venv) -and (Test-VenvMoved $venv)) {
        Report "WARNING" "Virtualenv location" "$(Split-Path (Split-Path $venv) -Leaf)\.venv was created in $(Split-Path (Get-VenvOrigin $venv)) - pytest.exe/uvicorn.exe/activate are broken; run scripts\development\setup.ps1 to rebuild"
    }
}
Check (Test-Path $aiExe) "AI service virtualenv" $(if (Test-Path $aiExe) { ".venv present" } else { "missing - run scripts\development\setup.ps1 (optional service)" }) "NOT CONFIGURED" -Optional
$modules = Join-Path $root "frontend\node_modules"
Check (Test-Path $modules) "Frontend packages" $(if (Test-Path $modules) { "node_modules present" } else { "missing - run scripts\development\setup.ps1" }) "NOT CONFIGURED"
foreach ($envFile in @("backend\SmartRation\.env", "frontend\.env")) {
    $present = Test-Path (Join-Path $root $envFile)
    Check $present $envFile $(if ($present) { "present (values not shown)" } else { "missing - copy the .env.example next to it and fill in the values" }) "NOT CONFIGURED"
}
if ($Deep) {
    & dotnet build (Join-Path $root "SmartRation.sln") -c Release --nologo -v q *> $null
    Check ($LASTEXITCODE -eq 0) ".NET build (Release)" $(if ($LASTEXITCODE -eq 0) { "SmartRation.sln builds" } else { "dotnet build SmartRation.sln -c Release failed - run it to see the errors" })
    if (Test-Path $modules) {
        Push-Location (Join-Path $root "frontend"); & npm run build --silent *> $null; $code = $LASTEXITCODE; Pop-Location
        Check ($code -eq 0) "Frontend build" $(if ($code -eq 0) { "vite build OK" } else { "npm run build failed - run it in frontend\ to see the errors" })
    }
}

# ------------------------------------------------------------------ services
if (-not $SkipServices) {
    Write-Host "`nServices" -ForegroundColor Cyan
    $frontend = Probe "http://localhost:5173/"
    Check ($frontend.Status -eq 200) "Frontend :5173" "HTTP $($frontend.Status)"

    $health = Probe "http://127.0.0.1:8000/health"
    $detail = "HTTP $($health.Status)"
    if ($health.Body) {
        $h = $health.Body | ConvertFrom-Json
        $detail = "status=$($h.status) database=$($h.database) legacyApi=$($h.legacyApi) aiService=$($h.aiService) chatbot=$($h.chatbot) dataMode=$($h.dataMode)"
    }
    if ($health.Status -eq 200 -and $health.Body -match '"status":"healthy"') { Report "PASS" "Python API :8000" $detail }
    elseif ($health.Status -eq 200) { Report "WARNING" "Python API :8000" "$detail (degraded)" }
    else { Report "FAIL" "Python API :8000" $detail }
    if ($health.Body) { Check ($health.Body -match '"chatbot":"healthy"') "Chatbot (knowledge base)" $(if ($health.Body -match '"chatbot":"healthy"') { "loaded, provider available" } else { "unhealthy - see the Python API log" }) }

    $ready = Probe "http://127.0.0.1:8000/ready"
    Check ($ready.Status -eq 200) "Ready for traffic" "HTTP $($ready.Status) /ready"
    $db = Probe "http://127.0.0.1:8000/health/db"
    Check ($db.Status -eq 200) "Database via API" $(if ($db.Body) { $db.Body } else { "HTTP $($db.Status) /health/db" })

    $legacy = Probe "http://localhost:5188/api/health"
    Check ($legacy.Status -eq 200) "C# API :5188" "HTTP $($legacy.Status)"
    $ai = Probe "http://127.0.0.1:8001/health"
    Check ($ai.Status -eq 200) "AI service :8001" $(if ($ai.Status -eq 200) { "HTTP 200" } else { "HTTP $($ai.Status) - optional; AI panels show 'unavailable'" }) "WARNING"

    # Another program on a service port (e.g. a Docker container publishing :8000) can answer requests
    # to "localhost" instead of this project's service - the browser then gets errors.
    foreach ($p in @(@{ Port = 5173; Expected = "^node" }, @{ Port = 8000; Expected = "^python" }, @{ Port = 5188; Expected = "^(dotnet|SmartRation\.Api)$" }, @{ Port = 8001; Expected = "^python" })) {
        $owners = @(Get-NetTCPConnection -LocalPort $p.Port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName } | Where-Object { $_ } | Sort-Object -Unique)
        $foreign = @($owners | Where-Object { $_ -notmatch $p.Expected })
        if ($foreign.Count) { Report "WARNING" "Port $($p.Port) shared" "also used by $($foreign -join ', ') - 'localhost' requests may reach it; stop it (e.g. its Docker container)" }
    }
}

# ------------------------------------------------------------------ database
Write-Host "`nDatabase" -ForegroundColor Cyan
if (Test-Path $pyExe) {
    Push-Location $pyDir
    $output = & $pyExe scripts\verify_database.py 2>&1 | Select-Object -Last 1
    Pop-Location
    Check ("$output" -match "PASSED") "MySQL schema + data" "$output"
} else {
    Report "NOT CONFIGURED" "MySQL schema + data" "Python API not set up - run scripts\development\setup.ps1"
}

Write-Host ""
$summary = "{0} passed, {1} failed, {2} warning(s), {3} not configured" -f $script:counts.PASS, $script:counts.FAIL, $script:counts.WARNING, $script:counts["NOT CONFIGURED"]
if ($script:blocking -eq 0) { Write-Host "HEALTHY: $summary." -ForegroundColor Green; exit 0 }
Write-Host "NOT HEALTHY: $summary. See docs\development\TROUBLESHOOTING.md." -ForegroundColor Red
exit 1
