# Security

## Secrets

| Secret | Where it lives | Never in |
|---|---|---|
| MySQL app password | `backend/SmartRation/.env` (`DATABASE_URL`), .NET user-secrets, `ai/.env` | git, logs, error messages, URLs printed by scripts (shown as `***`) |
| JWT signing key | `.env` `JWT_SECRET_KEY` = .NET user-secret `Jwt:Key` (same value, so tokens work on both) | git, logs |
| QR HMAC secret | .NET user-secret `Qr:Secret`; `.env` `QR_SECRET` when QR moves to Python | git, logs |
| Seed passwords | env vars `SEED_DEMO_PASSWORD`, `SEED_ADMIN_PASSWORD` at seed time only | source code |

`.env`, `.env.*` (except `.env.example`) and `database/backups/` are git-ignored. Docker images
contain no `.env` (see `.dockerignore`; CI asserts it); secrets are passed at run time. The Python
app refuses to start without `JWT_SECRET_KEY` and has no default for any secret.

**History:** before commit `4c983e2` the JWT key and QR secret were in the tracked
`appsettings.Development.json`, so they remain in git history. The QR secret was deliberately **not**
rotated (rotating it would invalidate every issued QR code). Before any public or production
deployment: rotate the JWT key (only effect: users log in again) and plan a QR secret rotation that
accepts the old secret for verification during a transition window.

## Authentication and authorisation

- JWT HS256, 15-minute access tokens, issuer `SmartRationHSD2C`, audience `SmartRationHSD2C.Clients`,
  role claim; validated for signature, expiry, issuer and audience.
- Refresh tokens: 64 random bytes, only the SHA-256 hash stored, rotated on every use (old one revoked
  and linked to its replacement), 7-day expiry, revoked on logout.
- Passwords: Argon2id for new hashes; legacy BCrypt hashes are verified and upgraded to Argon2id on
  the next successful login. Login failures give one generic message (no account enumeration) and
  are audited with a masked email.
- Rate limiting: login + register share 10 requests/minute per client IP (as in C#).
  Requests the Python proxy forwards carry `X-Forwarded-For`; the C# API trusts it from loopback
  proxies only (`UseForwardedHeaders`, fixed 2026-09-25), so its per-IP limits (QR scan, OTP) see the
  real client. The Python limiter keys on the client address that `app/middleware/edge.py` derives:
  `TRUSTED_PROXY_HOPS` entries from the right of `X-Forwarded-For` (0 = socket address, 1 = nginx, 2 = Render),
  never the left-most, client-controlled entry; uvicorn runs with `--no-proxy-headers` (security N1).
- Token storage (website): requests carry `X-Auth-Mode: cookie`, so the API keeps the refresh token in an HttpOnly,
  SameSite=Strict cookie (`sr_refresh`, path `/api`, Secure in production) and answers `refreshToken: null`. The
  access token lives in memory only; after a reload the first 401 refreshes from the cookie. `localStorage` holds
  only the user summary. The custom header is the CSRF guard (CORS allows it only for listed origins, without
  credentials). Website and API share one origin (the API serves the website; Vite proxies `/api` in development).
  The Android app keeps body mode (tokens in the JSON, stored in the OS keystore).
- Roles: `RuralUser`, `ShopOwner`, `GovernmentOfficial`, `Admin`, enforced per route with
  `require_roles(...)`, and ownership checks inside services (a user sees only their own data).

## Data protection

- No real Aadhaar or passbook data exists or is fetched; development data is synthetic, and Aadhaar
  values are masked references (`XXXX-XXXX-####`). Mobile numbers are shown masked (`******1234`).
- OTPs are stored hashed with attempt limits and expiry.
- QR codes carry an HMAC-signed reference (`SRQR-{tokenId}-{16 hex}`), not personal data.
- Ration collection is transactional and idempotent (unique idempotency key and one collection per token).
- Administrative actions and verification events are written to `AuditLogs` / `VerificationAuditLogs`.

## Public Help chatbot

Public and anonymous by design: it never reads personal data and ignores any `Authorization` header.
Questions about "my token / family / Aadhaar" get a log-in prompt; Aadhaar-like numbers, OTPs and
passwords typed into the chat trigger a warning and aren't processed; requests for internals or other
people's data are refused; health questions get general guidance only. Message text is never logged
(only kind, article id, language, length, duration). Replies are plain text rendered without HTML,
links are in-app paths only (validated server- and client-side). 30 messages/minute per client IP.
The conversation lives in the browser's `sessionStorage` only. Details: [CHATBOT.md](../chatbot/CHATBOT_ARCHITECTURE.md).

## Logging and errors

JSON log lines contain request id, method, path **without the query string**, status, duration and
serving backend. Passwords, OTPs, tokens, JWTs, database credentials and raw identifiers are never
logged. Error responses use the standard envelope and never include stack traces, SQL or file paths.

## Transport and input

- CORS allow-list from `CORS_ORIGINS` (default `http://localhost:5173`).
- Request bodies above `MAX_REQUEST_BYTES` (6 MB) are rejected with 413.
- All SQL goes through SQLAlchemy with bound parameters.
- In production, run behind TLS (reverse proxy) and set `ENVIRONMENT=production`; `reset_database.py`
  refuses to run in production.

## Database account

The app uses `smartration_app`, limited to the `smartration` schema; it cannot create databases or
read other schemas. Use root only for provisioning. Backups read credentials from environment
variables into a temporary option file that is deleted afterwards (never on the command line).

## Reporting

Report suspected vulnerabilities privately to the maintainer rather than in a public issue.
