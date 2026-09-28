# Native dependencies

**There is no C or C++ source code in this repository.** The migration brief assumed a C backend;
the Phase 0 audit ([MIGRATION_AUDIT.md](../migration/MIGRATION_AUDIT.md)) found the legacy backend is C#
(ASP.NET Core 8), which is what's being replaced.

The Python backend uses a few packages that ship compiled extensions. All install as prebuilt
wheels on Windows, macOS and Linux (x86-64 and arm64) for the Python versions in CI, so no compiler
is needed:

| Package | Native part | Used for |
|---|---|---|
| `argon2-cffi` (+ `argon2-cffi-bindings`) | Argon2 reference C library | password hashing |
| `bcrypt` | Rust extension | verifying legacy BCrypt hashes |
| `cryptography` | Rust + OpenSSL | used by PyJWT / PyMySQL auth |
| `pydantic-core` | Rust | request/response validation |
| `uvicorn[standard]` extras (`httptools`, `uvloop` on Linux, `watchfiles`) | C/Rust | HTTP server performance |
| `SQLAlchemy` | optional C extensions | ORM (falls back to pure Python) |

`PyMySQL` is pure Python, so no MySQL client library is required. The Docker image is based on
`python:3.13-slim` and installs only wheels.

Deliberately **not** used: OpenCV, PyTorch, YOLO or other computer-vision stacks (decision 4 of the
migration plan).

**Optional:** OCR of supporting documents (`ai/inference/ocr.py`) uses the external
Tesseract binary plus `pytesseract`/Pillow *only if they're installed*. Neither is in the requirements;
without them the OCR endpoint clearly reports that OCR is unavailable instead of returning fake text.
OCR is never identity verification; it only pre-fills fields a human confirms.
