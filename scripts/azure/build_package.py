"""Build the Azure App Service package: the API + the built website in one zip, laid out like the Docker image.

Only COMMITTED code goes in (git archive of a commit, default HEAD): uncommitted edits never reach production.

    python scripts/azure/build_package.py            # -> build/azure/smartration-app.zip
    python scripts/azure/build_package.py --ref main

Needs git, Node.js (npm) and Python on PATH. Contains no secrets: settings come from App Service at run time.
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "azure" / "smartration-app.zip"

# (path in the repository, path in the package): the same layout as backend/SmartRation/Dockerfile.
LAYOUT = [
    ("backend/SmartRation/alembic.ini", "alembic.ini"),
    ("backend/SmartRation/requirements.txt", "requirements.txt"),
    ("backend/SmartRation/app", "app"),
    ("backend/SmartRation/migrations", "migrations"),
    ("backend/SmartRation/scripts", "scripts"),
    ("backend/SmartRation/docker-entrypoint.sh", "docker-entrypoint.sh"),
    ("scripts/azure/startup.sh", "startup.sh"),
    ("ai/chatbot/knowledge", "ai/chatbot/knowledge"),
    ("database/seeds/synthetic", "database/seeds/synthetic"),
    ("database/queries", "database/queries"),
]
FRONTEND = ["frontend/package.json", "frontend/package-lock.json", "frontend/index.html", "frontend/vite.config.js",
            "frontend/public", "frontend/src"]
SKIP = ("__pycache__", ".pyc", ".pytest_cache")


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True, env=env, shell=sys.platform == "win32")


def export(ref: str, paths: list[str], dest: Path) -> None:
    """Extract `paths` of commit `ref` into dest (git archive: committed content only)."""
    data = subprocess.run(["git", "archive", "--format=tar", ref, "--", *paths], cwd=ROOT, check=True,
                          capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="HEAD", help="commit to package (default HEAD)")
    parser.add_argument("--demo-mode", default="true", choices=["true", "false"],
                        help="login page offers the synthetic demo accounts (VITE_DEMO_MODE)")
    args = parser.parse_args()
    commit = subprocess.run(["git", "rev-parse", "--short", args.ref], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="sr-azure-") as tmp:
        src, pkg = Path(tmp) / "src", Path(tmp) / "pkg"
        export(args.ref, [p for p, _ in LAYOUT] + FRONTEND, src)

        import os
        env = {**os.environ, "VITE_DEMO_MODE": args.demo_mode}
        env.pop("VITE_API_BASE_URL", None)   # same origin: the website calls /api on the host that served it
        run(["npm", "ci", "--no-audit", "--no-fund"], src / "frontend", env)
        run(["npm", "run", "build"], src / "frontend", env)

        for repo_path, pkg_path in LAYOUT:
            source, target = src / repo_path, pkg / pkg_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns(*SKIP))
            else:
                shutil.copy2(source, target)
        shutil.copytree(src / "frontend" / "dist", pkg / "frontend-dist")
        (pkg / "BUILD_COMMIT").write_text(commit + "\n", encoding="utf-8")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(pkg.rglob("*")):
                if file.is_file():
                    info = zipfile.ZipInfo.from_file(file, file.relative_to(pkg).as_posix())
                    if file.suffix == ".sh":
                        info.external_attr = 0o100755 << 16   # executable on Linux
                    info.compress_type = zipfile.ZIP_DEFLATED
                    data = file.read_bytes()
                    if file.suffix == ".sh":
                        data = data.replace(b"\r\n", b"\n")   # Windows checkouts: sh fails on CRLF
                    zf.writestr(info, data)
    print(f"built {OUT.relative_to(ROOT)} from commit {commit} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
