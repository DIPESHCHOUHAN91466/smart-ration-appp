#!/usr/bin/env bash
# First-time (or refresh) development setup for macOS/Linux (and Git Bash). Same steps as setup.ps1:
#   tools check -> Python virtualenvs + requirements -> npm install -> dotnet restore ->
#   copy each .env.example to .env ONLY if .env is missing (never overwrites).
# No database is created or changed. Usage: scripts/development/setup.sh [--check-only]
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHECK_ONLY=0; [ "${1:-}" = "--check-only" ] && CHECK_ONLY=1
FAILED=0
ok()   { printf '\033[32m[OK]\033[0m      %s\n' "$1"; }
todo() { printf '\033[33m[TODO]\033[0m    %s\n' "$1"; }
err()  { printf '\033[31m[ERROR]\033[0m   %s\n' "$1"; FAILED=$((FAILED + 1)); }
run()  {  # run <description> <directory> <command...>
  local description="$1" dir="$2"; shift 2
  if [ "$CHECK_ONLY" = 1 ]; then todo "would run: $description"; return; fi
  if (cd "$dir" && "$@"); then ok "$description"; else err "$description failed in $dir"; fi
}

echo "== Tools"
PYTHON="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON" ]; then err "Python 3.12+ MISSING - https://www.python.org/downloads/"
elif "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then ok "Python: $("$PYTHON" --version 2>&1)"
else err "Python WRONG VERSION ($("$PYTHON" --version 2>&1)) - need 3.12+"; fi
if command -v dotnet >/dev/null && dotnet --version | grep -Eq '^(8|9|1[0-9])\.'; then ok ".NET SDK: $(dotnet --version)"; else err ".NET 8 SDK MISSING or too old - https://dotnet.microsoft.com/download/dotnet/8.0"; fi
if command -v node >/dev/null && node --version | grep -Eq '^v(1[89]|[2-9][0-9])\.'; then ok "Node.js: $(node --version)"; else err "Node.js 18+ MISSING or too old - https://nodejs.org"; fi
if command -v npm >/dev/null; then ok "npm: $(npm --version)"; else err "npm MISSING (comes with Node.js)"; fi
[ "$FAILED" -gt 0 ] && { echo "Install the missing tools and run this script again."; exit 1; }

for spec in "backend/SmartRation:requirements-dev.txt" "backend/SmartRation.AI:requirements.txt"; do
  dir="$ROOT/${spec%%:*}"; req="${spec##*:}"
  echo "== ${spec%%:*}"
  if [ -d "$dir/.venv" ]; then ok ".venv exists"; else run "python -m venv .venv" "$dir" "$PYTHON" -m venv .venv; fi
  venv_python="$dir/.venv/bin/python"; [ -x "$venv_python" ] || venv_python="$dir/.venv/Scripts/python.exe"  # Git Bash on Windows
  run "pip install -r $req" "$dir" "$venv_python" -m pip install --disable-pip-version-check -q -r "$req"
done

echo "== Frontend"
run "npm install" "$ROOT/frontend" npm install --no-fund --no-audit
echo "== C# API"
run "dotnet restore SmartRation.sln" "$ROOT" dotnet restore SmartRation.sln --nologo -v q

echo "== .env files"
for dir in "." "backend/SmartRation" "backend/SmartRation.AI" "frontend"; do
  [ -f "$ROOT/$dir/.env.example" ] || continue
  if [ -f "$ROOT/$dir/.env" ]; then ok "$dir/.env exists (left unchanged)"
  elif [ "$CHECK_ONLY" = 1 ]; then todo "would create $dir/.env from .env.example"
  else cp "$ROOT/$dir/.env.example" "$ROOT/$dir/.env"; todo "created $dir/.env - fill in the database password and secrets"; fi
done

if [ "$FAILED" -gt 0 ]; then echo "$FAILED step(s) failed - read the messages above."; exit 1; fi
echo "Setup complete. Next: seed the database (scripts/database/seed-demo-data.ps1 or backend/SmartRation/scripts/setup_database.py + seed_database.py), then start the services (docs/development/LOCAL_SETUP.md)."
