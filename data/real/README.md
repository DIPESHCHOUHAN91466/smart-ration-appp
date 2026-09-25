# data/real — what real data would require

**Status: BLOCKED — REQUIRES EXTERNAL INTEGRATION.** This folder holds no data and never should: real
personal data does not belong in a source repository. With `DATA_MODE=real`, both backends refuse to
start today, because no real provider exists yet.

## What must exist before real data

| Integration | Replaces | Needs |
|---|---|---|
| State PDS / ration-card registry API | `SyntheticDataProvider` (Python), `SyntheticPassbookVerificationService` (C#) | a data-sharing agreement with the state Food & Civil Supplies department, API contract, credentials |
| Aadhaar authentication / eKYC | `SyntheticAadhaarVerificationService` (C#) | access through a UIDAI-licensed AUA/KUA; the app must never store full Aadhaar numbers |
| SMS gateway | `MockSmsProvider` (C#) | a DLT-registered sender and templates; `Sms:Provider=Http` (adapter exists) |
| Real reference data (shops, schemes, quotas) | `data/synthetic/reference` | official sources and an update process |

## Before switching (all required)

1. A **separate production database** — never load real data into the demo database or `smartration_test`.
2. **Privacy and consent** — purpose, consent capture and retention under the Digital Personal Data
   Protection Act, 2023; Aadhaar Act restrictions.
3. **Security review** — penetration test; rotate the JWT key (it is in old git history); refresh token
   in an HttpOnly cookie; audit-log retention; backup + tested restore; TLS everywhere.
4. **Implement the real providers** behind the existing interfaces (`app/data_providers`,
   `Services/Verification/I*.cs`) — business code does not change.
5. **Remove the startup refusal** for real mode only once 1–4 are signed off
   (`DataModeGuard.cs`, `app/data_providers/check_data_mode`).

Design: [../../docs/architecture/DATA_ARCHITECTURE.md](../../docs/architecture/DATA_ARCHITECTURE.md).
