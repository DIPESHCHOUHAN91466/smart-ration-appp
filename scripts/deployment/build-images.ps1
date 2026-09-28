<#
.SYNOPSIS
  Builds both deployable Docker images from the repository root, exactly as render.yaml / CI build them.

.DESCRIPTION
  smartration-api:<tag>   backend/SmartRation/Dockerfile      Python gateway + the built website
  smartration-csharp-api:<tag>  backend/SmartRation.Api/Dockerfile  C# business API
  The build context is the repository root; .dockerignore is an allow-list, so secrets, backups,
  virtualenvs and node_modules cannot enter an image. Nothing is pushed anywhere.

.EXAMPLE
  .\scripts\deployment\build-images.ps1
  .\scripts\deployment\build-images.ps1 -Tag rehearsal -DemoMode
#>
param(
    [string]$Tag = "local",
    [switch]$DemoMode   # bake VITE_DEMO_MODE=true into the website (the login page lists the synthetic demo accounts)
)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker is not installed or not on PATH." }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker is installed but the engine is not running (start Docker Desktop)." }

$images = @(
    @{ Name = "smartration-api:$Tag";  File = "backend/SmartRation/Dockerfile";     Args = @("--build-arg", "VITE_DEMO_MODE=$(if ($DemoMode) { 'true' } else { 'false' })") },
    @{ Name = "smartration-csharp-api:$Tag"; File = "backend/SmartRation.Api/Dockerfile"; Args = @() }
)
Push-Location $root
try {
    foreach ($image in $images) {
        Write-Host "== docker build $($image.Name) ($($image.File))" -ForegroundColor Cyan
        docker build -f $image.File -t $image.Name @($image.Args) .
        if ($LASTEXITCODE -ne 0) { throw "Build failed: $($image.Name)" }
    }
}
finally { Pop-Location }

docker image ls --format "{{.Repository}}:{{.Tag}}  {{.Size}}" | Select-String -Pattern ":$Tag\s"
Write-Host "Images built. Run them with docker-compose.yml, or push through your host's pipeline (render.yaml builds its own)." -ForegroundColor Green
