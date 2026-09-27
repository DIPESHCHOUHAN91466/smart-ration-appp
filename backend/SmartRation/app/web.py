"""Serve the built React frontend (frontend/dist) from this API, for single-service deployments.

Enabled only when FRONTEND_DIST_DIR points at a build (the Docker image sets it). The browser then loads
the app and calls the API on the same origin ("/api"), so no CORS or cross-service URL is needed.
Local development doesn't use this: Vite serves the frontend on :5173.

Routing: registered LAST, for GET only. API, health and docs paths are never answered with the app;
an existing file under the build is served; any other path gets index.html so client-side routes
(/rural/dashboard, /help, ...) work on reload.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

RESERVED = ("api/", "docs", "redoc", "openapi.json", "health", "ready")
_HTML_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=(self)",  # camera: QR scanner
}


def mount_frontend(app: FastAPI, dist_dir: str) -> None:
    root = Path(dist_dir).resolve()
    index = root / "index.html"
    if not index.is_file():
        raise RuntimeError(f"FRONTEND_DIST_DIR={dist_dir} has no index.html (build the frontend first).")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str) -> FileResponse:
        if path.startswith(RESERVED):
            raise HTTPException(status_code=404)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):   # never outside the build
            immutable = candidate.parent.name == "assets"                      # hashed file names: cache forever
            headers = {"Cache-Control": "public, max-age=31536000, immutable" if immutable else "public, max-age=3600",
                       "X-Content-Type-Options": "nosniff"}
            return FileResponse(candidate, headers=headers)
        return FileResponse(index, headers=_HTML_HEADERS)
