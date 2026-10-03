"""Serve the built React frontend (frontend/dist) from this API, for single-service deployments.

Enabled only when FRONTEND_DIST_DIR points at a build (the Docker image sets it). The browser then loads
the app and calls the API on the same origin ("/api"), so no CORS or cross-service URL is needed.
Local development doesn't use this: Vite serves the frontend on :5173.

Routing: registered LAST, for GET only. API, health and docs paths are never answered with the app;
an existing file under the build is served; any other path gets index.html so client-side routes
(/rural/dashboard, /help, ...) work on reload.

Compression: the website's text files (scripts, styles, SVG, JSON, the page itself) are sent gzip-compressed to
browsers that accept it, compressed once and kept in memory (build files never change: hashed names). API responses
are deliberately NOT compressed: compressing responses that mix secrets (tokens) with user-supplied text enables
BREACH-style attacks.
"""

from __future__ import annotations

import gzip
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response

RESERVED = ("api/", "docs", "redoc", "openapi.json", "health", "ready")
_HTML_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # camera: QR scanner; microphone: the help chatbot's voice input (it was "()", which silently blocked it)
    "Permissions-Policy": "camera=(self), microphone=(self), geolocation=(self)",
    # Only what the built website really loads: its own files (fonts included), OpenStreetMap tiles for the shop map, and
    # its own QR-decoder worker. No inline or eval'd script. Inline style attributes are allowed (React style={...}).
    "Content-Security-Policy": "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self' data:",
        "img-src 'self' data: blob: https://*.tile.openstreetmap.org",
        "connect-src 'self'",
        "worker-src 'self' blob:",
        "media-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]),
}
_COMPRESSIBLE = {".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".html": "text/html",
                 ".svg": "image/svg+xml", ".json": "application/json", ".txt": "text/plain", ".webmanifest": "application/manifest+json"}
_MIN_COMPRESS_BYTES = 1024


def _accepts_gzip(request: Request) -> bool:
    return "gzip" in request.headers.get("accept-encoding", "").lower()


def mount_frontend(app: FastAPI, dist_dir: str) -> None:
    root = Path(dist_dir).resolve()
    index = root / "index.html"
    if not index.is_file():
        raise RuntimeError(f"FRONTEND_DIST_DIR={dist_dir} has no index.html (build the frontend first).")
    compressed: dict[Path, bytes] = {}            # file -> gzip bytes (build files are immutable while running)

    def send(file: Path, headers: dict[str, str], request: Request) -> Response:
        media_type = _COMPRESSIBLE.get(file.suffix.lower())
        if media_type and _accepts_gzip(request) and file.stat().st_size >= _MIN_COMPRESS_BYTES:
            if file not in compressed:
                compressed[file] = gzip.compress(file.read_bytes(), compresslevel=9)
            return Response(compressed[file], media_type=media_type,
                            headers={**headers, "Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
        return FileResponse(file, headers={**headers, "Vary": "Accept-Encoding"} if media_type else headers)

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str, request: Request) -> Response:
        if path.startswith(RESERVED):
            raise HTTPException(status_code=404)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):   # never outside the build
            immutable = candidate.parent.name == "assets"                      # hashed file names: cache forever
            headers = {"Cache-Control": "public, max-age=31536000, immutable" if immutable else "public, max-age=3600",
                       "X-Content-Type-Options": "nosniff"}
            return send(candidate, headers, request)
        return send(index, _HTML_HEADERS, request)
