# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** to the project maintainers (HSD2C), not in a
public issue. Include what you found, how to reproduce it, and its impact. Do not access, change or
download other people's data while testing; use the synthetic demo accounts.

## Scope and architecture

The full security architecture — secrets handling, authentication and authorisation, data protection
(masked Aadhaar, hashed OTPs, signed QR codes), logging rules, rate limits, the Public Help chatbot's
privacy rules, and the known open items — is documented in [docs/security/SECURITY_ARCHITECTURE.md](docs/security/SECURITY_ARCHITECTURE.md).

## Known open items (summary)

- Website sessions: the refresh token is an HttpOnly, SameSite=Strict cookie (`sr_refresh`, path `/api`) and is
  never in a response body or in `localStorage`; the access token is kept in memory only (security S7, 2026-10-06).
- The JWT signing key existed in git history before commit `4c983e2`; rotate it before any public
  deployment. The QR secret was intentionally kept (rotating it invalidates issued QR codes).
- This installation uses synthetic data only and is not connected to any government system.
