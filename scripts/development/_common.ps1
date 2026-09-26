# Helpers shared by the development scripts (dot-source it: . "$PSScriptRoot\_common.ps1").

# The folder a Python virtualenv was created in, read from its pyvenv.cfg ("command = ... -m venv <path>").
# $null when it can't be told (older Python versions don't write the command line).
function Get-VenvOrigin([string]$VenvDir) {
    $cfg = Join-Path $VenvDir "pyvenv.cfg"
    if (-not (Test-Path $cfg)) { return $null }
    $line = Get-Content $cfg | Where-Object { $_ -match "^command\s*=" } | Select-Object -First 1
    # Skip options such as --clear / --upgrade-deps that may sit between "-m venv" and the path.
    if ($line -match "-m venv\s+(?:--?[\w-]+\s+)*(.+?)\s*$") { return $Matches[1].Trim('"') }
    return $null
}

# True when the virtualenv was created in a different folder (the project was moved or copied). Such a
# virtualenv still runs "python -m ...", but its .exe launchers (pytest.exe, uvicorn.exe) and activate
# scripts point to the old location and fail. Rebuild it: scripts\development\setup.ps1.
function Test-VenvMoved([string]$VenvDir) {
    $origin = Get-VenvOrigin $VenvDir
    if (-not $origin) { return $false }
    try {
        $here = [IO.Path]::GetFullPath($VenvDir).TrimEnd('\')
        return -not [string]::Equals([IO.Path]::GetFullPath($origin).TrimEnd('\'), $here, [StringComparison]::OrdinalIgnoreCase)
    } catch {
        return $false   # an unreadable origin is not evidence of a move
    }
}
