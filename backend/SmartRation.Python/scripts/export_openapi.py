"""Write the API contracts in api/openapi/ (generated, read-only; never edit them by hand).

    .venv\\Scripts\\python scripts\\export_openapi.py            # rewrite python-api.openapi.json
    .venv\\Scripts\\python scripts\\export_openapi.py --check    # exit 1 if it is out of date (tests run this)
    .venv\\Scripts\\python scripts\\export_openapi.py --csharp http://localhost:5188
        # also save csharp-api.swagger.json from a RUNNING C# API (Development mode serves /swagger)

The Python contract is built from the code itself (FastAPI's OpenAPI generator): no server, no database,
and throwaway settings, so nothing secret can end up in the file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

OUT = ROOT.parents[1] / "api" / "openapi"
PYTHON_CONTRACT = OUT / "python-api.openapi.json"
CSHARP_CONTRACT = OUT / "csharp-api.swagger.json"


def render_python() -> str:
    settings = Settings(_env_file=None, database_url="sqlite://", jwt_secret_key="contract-export-only-" + "0" * 32,
                        legacy_api_url="", ai_service_url="")
    return json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    args = sys.argv[1:]
    document = render_python()
    if "--check" in args:
        current = PYTHON_CONTRACT.read_text(encoding="utf-8") if PYTHON_CONTRACT.exists() else ""
        if current != document:
            print(f"{PYTHON_CONTRACT} is out of date: run scripts/export_openapi.py")
            return 1
        print("Python API contract is up to date.")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    PYTHON_CONTRACT.write_text(document, encoding="utf-8", newline="\n")
    print(f"Wrote {PYTHON_CONTRACT} ({len(json.loads(document)['paths'])} paths)")
    if "--csharp" in args:
        import httpx

        base = args[args.index("--csharp") + 1].rstrip("/")
        swagger = httpx.get(f"{base}/swagger/v1/swagger.json", timeout=10).raise_for_status().json()
        CSHARP_CONTRACT.write_text(json.dumps(swagger, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"Wrote {CSHARP_CONTRACT} ({len(swagger['paths'])} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
