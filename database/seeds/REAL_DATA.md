# Real data — what it would require

**Status: BLOCKED — REQUIRES EXTERNAL INTEGRATION.** No real data is stored in this repository, and none ever should be: real
personal data does not belong in a source repository. With `DATA_MODE=real`, both backends refuse to
start today, because no real provider exists yet.

## What must exist before real data

| Integration | Replaces | Needs |
|---|---|---|
| State PDS / ration-card registry API | `SyntheticDataProvider` (Python), `SyntheticPassbookVerificationService` (C#) | a data-sharing agreement with the state Food & Civil Supplies department, API contract, credentials |
| Aadhaar authentication / eKYC | `SyntheticAadhaarVerificationService` (C#) | access through a UIDAI-licensed AUA/KUA; the app must never store full Aadhaar numbers |
| SMS gateway | `MockSmsProvider` (C#) | a DLT-registered sender and templates; `Sms:Provider=Http` (adapter exists) |
| Real reference data (shops, schemes, quotas) | `database/seeds/synthetic` | official sources and an update process |

## Before switching (all required)

1. A **separate production database** — never load real data into the demo database or `smartration_test`.
2. **Privacy and consent** — purpose, consent capture and retention under the Digital Personal Data
   Protection Act, 2023; Aadhaar Act restrictions.
3. **Security review** — penetration test; rotate the JWT key (it is in old git history); refresh token
   in an HttpOnly cookie; audit-log retention; backup + tested restore; TLS everywhere.
4. **Implement the real providers** behind the existing interfaces (`app/services/data_provider.py`,
   `Services/Verification/I*.cs`) — business code does not change.
5. **Remove the startup refusal** for real mode only once 1–4 are signed off
   (`DataModeGuard.cs`, `app/services/data_provider.py/check_data_mode`).

Design: [../../docs/architecture/DATA_ARCHITECTURE.md](../../docs/architecture/DATA_ARCHITECTURE.md).


## Transition plan: synthetic → authorised real data (prepared 2026-10-18; nothing imported)

**Timing:** the owner aims for next month. Each step below is a gate, and the data-sharing agreement and Aadhaar
access usually take longer than a month. The synthetic demo keeps running until every gate is signed off.

**How synthetic data is marked today:**
- `DATA_MODE=synthetic`; the API reports `dataMode: synthetic` and `isSyntheticData: true`.
- Map markers carry `dataSource: SYNTHETIC_DEMO`.
- Prefixes: ration cards `SYN-RC-…`, QR references `SRQR-DEMO-…`, collection codes `COL-DEMO-…`.
- Aadhaar is only ever stored masked (`XXXX-XXXX-1234`).
- Real records must never use these prefixes, so the two can never be confused.

| # | Step | What it takes | Owner / evidence |
|---|---|---|---|
| 1 | **Legal basis** | a written data-sharing agreement or MoU with the state Food & Civil Supplies department (or the district authority), naming the purpose (slot booking and collection only), the fields, retention, and who is the data fiduciary | owner; signed agreement on file |
| 2 | **Privacy notice and consent** | update the privacy policy (web `/privacy`, app `PRIVACY_POLICY.md`) to the actual fiduciary, purpose, retention and grievance officer, per the DPDP Act 2023 and Rules. Record citizen consent where the law requires it; registration already requires privacy consent | owner and legal; published notice |
| 3 | **Minimisation** | import only: ration-card number, head and member names, member count and eligibility, scheme, shop code, a mobile number for booking. **No full Aadhaar**; verification through a UIDAI-licensed AUA/KUA only, or not at all | data mapping sheet signed off |
| 4 | **Field mapping and validation** | a written mapping from the source schema to `Families` / `Beneficiaries` / `FamilyMembers` / `RationShops` / schemes. A validation script rejects bad mobile numbers, unknown shop codes, missing quotas and duplicate card numbers | script plus test fixtures (synthetic) |
| 5 | **Duplicate detection** | by ration-card number (unique); mobile reuse across families flagged for review, never merged automatically | report in the dry run |
| 6 | **Data quality** | counts per district and shop, quota totals, eligibility distribution, compared with the source's own totals | reconciliation report |
| 7 | **Access control and audit** | real data only in a **separate production database**, never in the demo database or `smartration_test`. The least-privilege runtime account (SEC-04) is verified; staff accounts provisioned by an administrator only (self-registration is always a citizen, already enforced and tested); audit log retained | access review |
| 8 | **Encryption** | in transit: TLS to MySQL (enforced on Azure) and HTTPS only. At rest: Azure MySQL storage encryption (on by default), backups encrypted. The import file itself is transferred over SFTP or HTTPS and deleted after the import | checklist |
| 9 | **Retention and deletion** | the retention period from step 1; account closure and export already exist (`/api/users/me/close`, `/api/users/me/export`); erasure follows the agreed retention | policy document |
| 10 | **Backup and restore** | an Azure point-in-time restore drill into a temporary server **before** the import (approval needed) | drill record |
| 11 | **Isolated dry run** | import into a throwaway copy of the production schema (a new temporary database or server, never production), run steps 4–6, then the E2E and smoke suites against it, then delete it | dry-run report |
| 12 | **Go-live** | providers implemented behind `app/services/data_provider.py`; the `DATA_MODE=real` startup refusal removed only after steps 1–11 are signed off; real SMS through a DLT-registered gateway (the honest 503 until then) | owner approval |
| 13 | **Rollback** | keep the pre-import backup. If reconciliation fails after go-live, stop bookings (maintenance page), restore the backup into a new server, and repoint the app | runbook |
| 14 | **Incident response** | a named contact; report breaches as the DPDP Act and Rules require (Data Protection Board, affected people) and to CERT-In within its time limit; rotate credentials; preserve logs | incident runbook |

**Never:** scrape, buy, invent or copy-paste real Aadhaar numbers or ration-holder records; load real data on a
developer PC; commit any real record to Git.
