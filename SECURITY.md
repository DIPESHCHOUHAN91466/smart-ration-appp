# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** to the project maintainers (HSD2C) at **[SECURITY CONTACT EMAIL]**,
not in a public issue. Include what you found, how to reproduce it, and its impact. Do not access, change or download
other people's data while testing; use the synthetic demo accounts. We acknowledge reports within 3 working days and
tell you what we will do and when.

## Scope and architecture

The security architecture — secrets, authentication (Argon2id, 12+ character passwords, refresh-token rotation with
reuse detection, HttpOnly session cookie on the website, optional TOTP two-factor sign-in for staff), authorisation
(role and shop scoping, deny by default), data protection (masked Aadhaar, hashed OTPs and reset codes, signed QR
codes, encrypted TOTP secrets), logging, rate limits and the AI features' privacy rules — is documented in
[docs/security/SECURITY_ARCHITECTURE.md](docs/security/SECURITY_ARCHITECTURE.md). Findings, fixes and test evidence are in
[SECURITY_REPORT.md](SECURITY_REPORT.md).

## Incident response checklist

When a security incident is suspected (leaked secret, unexpected admin action, data seen by the wrong person,
service abuse):

1. **Record** the time, who noticed, and what was seen. Keep the request ids (`X-Request-ID`) of suspicious requests.
2. **Contain**
   - leaked `JWT_SECRET_KEY`: replace it — every session ends and everyone signs in again;
   - leaked `QR_SECRET`: replace it — every issued QR code stops working (citizens re-open their token to get a new one);
   - leaked `MFA_ENCRYPTION_KEY`: replace it, then clear `TotpSecret`/`TotpEnabledAt` for staff so they set up again;
   - a compromised account: deactivate it (its sessions end at the next refresh, within 15 minutes) or reset its password;
   - leaked database credentials: change the password at the provider and in the deployment's secret store;
   - abuse from one address: block it at the hosting provider / reverse proxy.
3. **Preserve evidence** before cleaning up: take a database backup (`scripts/database/backup.ps1`) and export the
   logs. Security events are structured log lines from logger `smartration.security` (`permission_denied`,
   `rate_limited`, `payload_too_large`); sign-in and account events are in the `AuditLogs` table
   (`LOGIN_FAILED`, `LOGIN_LOCKED`, `REFRESH_TOKEN_REUSED`, `PASSWORD_CHANGED`, `PASSWORD_RESET`, `MFA_*`, …).
4. **Assess** what was accessed and whose data: audit log by user and time, request logs by path and request id.
5. **Recover**: fix the cause, deploy through CI (tests, dependency audit, gitleaks, semgrep must pass), verify.
6. **Notify**: report cyber-security incidents to **CERT-In within 6 hours** of noticing them (CERT-In Directions,
   28 April 2022), and personal-data breaches to the **Data Protection Board and the affected people** (DPDP Act 2023
   and its Rules). The operator, not the developers, is responsible for these notifications.
7. **Review** within two weeks: what failed, what changes, and update this file and SECURITY_REPORT.md.

## Known open items (summary)

- The JWT and QR signing secrets in git history (commit 972d853) are public forever: servers refuse them outside
  development, every deployment generates its own, and the local values were rotated on 2026-10-06.
- The Android app has no two-factor code step and no password change/reset screens yet.
- Citizens can download their data (Settings → Download my data) but not yet ask for deletion: retention rules for
  public-distribution records must be decided by the operator first.
- Least-privilege database accounts are supported (`database/schema/mysql-least-privilege.sql`) but must be applied by
  the database owner in each environment.
- This installation uses synthetic data only and is not connected to any government system.
