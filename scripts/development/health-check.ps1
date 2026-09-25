<#
.SYNOPSIS
  Check the tools, the project setup and every running Smart Ration component. Read-only.

.DESCRIPTION
  Prints one line per check: [OK], [WARNING] (optional or degraded) or [ERROR] (must be fixed).
    Tools     Python, .NET 8 SDK, Node.js, npm, Git, MySQL server (+ optional mysql client, Docker)
    Project   solution file, Python virtualenvs, Python imports, frontend packages, .env files
    Services  frontend :5173, Python API :8000 (/health, /ready, /health/db), C# API :5188, AI :8001
    Database  schema, migration version and reference data (backend\SmartRation.Python\scripts\verify_database.py)
  Works from any current directory. Exit code 0 when there are no errors (warnings allowed), 1 otherwise.
  -SkipServices checks only tools, project and database (useful before anything is started).

.EXAMPLE
  .\scripts\development\health-check.ps1
  .\scripts\development\health-check.ps1 -SkipServices
#>
param([switch]$SkipServices)
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$script:errors = 0
$script:warnings = 0

function Report([string]$Level, [string]$Name, [string]$Detail) {
    $color = @{ OK = "Green"; WARNING = "Yellow"; ERROR = "Red" }[$Level]
    Write-Host ("{0,-10} {1,-26} {2}" -f "[$Level]", $Name, $Detail) -ForegroundColor $color
    if ($Level -eq "ERROR") { $script:errors++ }
    if ($Level -eq "WARNING") { $script:warnings++ }
}

function Check([bool]$Ok, [string]$Name, [string]$Detail, [string]$FailLevel = "ERROR") {
    Report $(if ($Ok) { "OK" } else { $FailLevel }) $Name $Detail
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
$py = Version "python" @("--version")
Check ($py -match "Python 3\.(1[2-9]|[2-9]\d)") "Python 3.12+" $(if ($py) { $py } else { "MISSING - install from https://www.python.org/downloads/" })
$dotnet = Version "dotnet" @("--version")
Check ($dotnet -match "^(8|9|1\d)\.") ".NET SDK 8+" $(if ($dotnet) { $dotnet } else { "MISSING - install the .NET 8 SDK from https://dotnet.microsoft.com/download" })
$node = Version "node" @("--version")
Check ($node -match "^v(1[89]|[2-9]\d)\.") "Node.js 18+" $(if ($node) { $node } else { "MISSING - install Node.js LTS from https://nodejs.org" })
$npm = Version "npm" @("--version")
Check ([bool]$npm) "npm" $(if ($npm) { $npm } else { "MISSING - comes with Node.js" })
$git = Version "git" @("--version")
Check ([bool]$git) "Git" $(if ($git) { $git } else { "MISSING - install from https://git-scm.com" }) "WARNING"
$mysqlService = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
$mysqlPort = [bool](Get-NetTCPConnection -LocalPort 3306 -State Listen -ErrorAction SilentlyContinue)
Check $mysqlPort "MySQL server :3306" $(if ($mysqlPort) { "listening" + $(if ($mysqlService) { " (service MySQL80: $($mysqlService.Status))" }) } elseif ($mysqlService) { "service MySQL80 is $($mysqlService.Status) - Start-Service MySQL80 (as administrator)" } else { "NOT FOUND - install MySQL 8 Community Server" })
$client = Version "mysql" @("--version")
Check ([bool]$client) "mysql client on PATH" $(if ($client) { $client } else { "not on PATH (optional; only backup/restore scripts use it)" }) "WARNING"
$docker = Version "docker" @("--version")
if (-not $docker) { Report "WARNING" "Docker (optional)" "not installed (only needed for docker-compose)" }
else {
    & docker info --format "{{.ServerVersion}}" *> $null
    $engine = ($LASTEXITCODE -eq 0)
    Check $engine "Docker (optional)" $(if ($engine) { "$docker, engine running" } else { "$docker, engine NOT running (start Docker Desktop to use docker-compose)" }) "WARNING"
}

# ------------------------------------------------------------------ project
Write-Host "`nProject ($root)" -ForegroundColor Cyan
Check (Test-Path (Join-Path $root "SmartRation.sln")) "Solution file" "SmartRation.sln"
$pyDir = Join-Path $root "backend\SmartRation.Python"
$pyExe = Join-Path $pyDir ".venv\Scripts\python.exe"
Check (Test-Path $pyExe) "Python API virtualenv" $(if (Test-Path $pyExe) { ".venv present" } else { "missing - run scripts\development\setup.ps1" })
if (Test-Path $pyExe) {
    Push-Location $pyDir
    $imports = & $pyExe -c "import app.main, app.synthetic, app.db.database; print('ok')" 2>&1 | Select-Object -Last 1
    Pop-Location
    Check ("$imports" -eq "ok") "Python API imports" $(if ("$imports" -eq "ok") { "app.main, app.synthetic, app.db.database" } else { "$imports" })
}
$aiExe = Join-Path $root "backend\SmartRation.AI\.venv\Scripts\python.exe"
Check (Test-Path $aiExe) "AI service virtualenv" $(if (Test-Path $aiExe) { ".venv present" } else { "missing - run scripts\development\setup.ps1 (optional service)" }) "WARNING"
$modules = Join-Path $root "frontend\node_modules"
Check (Test-Path $modules) "Frontend packages" $(if (Test-Path $modules) { "node_modules present" } else { "missing - run scripts\development\setup.ps1" })
foreach ($envFile in @("backend\SmartRation.Python\.env", "frontend\.env")) {
    $present = Test-Path (Join-Path $root $envFile)
    Check $present $envFile $(if ($present) { "present (values not shown)" } else { "missing - copy the .env.example next to it and fill in the values" })
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
    if ($health.Status -eq 200 -and $health.Body -match '"status":"healthy"') { Report "OK" "Python API :8000" $detail }
    elseif ($health.Status -eq 200) { Report "WARNING" "Python API :8000" "$detail (degraded)" }
    else { Report "ERROR" "Python API :8000" $detail }

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
    Report "ERROR" "MySQL schema + data" "Python API not set up"
}

Write-Host ""
if ($script:errors -eq 0) {
    Write-Host ("No errors ({0} warning(s))." -f $script:warnings) -ForegroundColor Green
    exit 0
}
Write-Host ("{0} error(s), {1} warning(s). See docs\development\TROUBLESHOOTING.md." -f $script:errors, $script:warnings) -ForegroundColor Red
exit 1
